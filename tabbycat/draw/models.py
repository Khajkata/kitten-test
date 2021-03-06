import logging

from django.db import models
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

from tournaments.utils import get_position_name

from .generator import DRAW_FLAG_DESCRIPTIONS

logger = logging.getLogger(__name__)


class DebateManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return super().get_queryset().select_related('round')


class Debate(models.Model):
    STATUS_NONE = 'N'
    STATUS_POSTPONED = 'P'
    STATUS_DRAFT = 'D'
    STATUS_CONFIRMED = 'C'
    STATUS_CHOICES = ((STATUS_NONE, 'None'),
                      (STATUS_POSTPONED, 'Postponed'),
                      (STATUS_DRAFT, 'Draft'),
                      (STATUS_CONFIRMED, 'Confirmed'), )

    objects = DebateManager()

    round = models.ForeignKey('tournaments.Round', models.CASCADE, db_index=True)
    venue = models.ForeignKey('venues.Venue', models.SET_NULL, blank=True, null=True)
    # cascade to keep draws clean in event of division deletion
    division = models.ForeignKey('divisions.Division', models.CASCADE, blank=True, null=True)

    bracket = models.FloatField(default=0)
    room_rank = models.IntegerField(default=0)

    time = models.DateTimeField(blank=True, null=True,
        help_text="The time/date of a debate if it is specifically scheduled")

    # comma-separated list of strings
    flags = models.CharField(max_length=100, blank=True)

    importance = models.IntegerField(default=0)
    result_status = models.CharField(max_length=1, choices=STATUS_CHOICES, default=STATUS_NONE)
    ballot_in = models.BooleanField(default=False)

    def __str__(self):
        description = "[{}/{}/{}] ".format(self.round.tournament.slug, self.round.abbreviation, self.id)
        try:
            description += self.matchup
        except:
            logger.critical("Error rendering Debate.matchup in Debate.__str__", exc_info=True)
            description += "<error showing teams>"
        return description

    @property
    def matchup(self):
        # This method is used by __str__, so it's not allowed to crash (ever)
        try:
            return "%s vs %s" % (self.aff_team.short_name, self.neg_team.short_name)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            dts = self.debateteam_set.all()
            if all(dt.position == DebateTeam.POSITION_UNALLOCATED for dt in dts):
                return ", ".join([dt.team.short_name for dt in dts])
            else:
                return self._teams_and_positions_display()

    def _teams_and_positions_display(self):
        return ", ".join(["%s (%s)" % (dt.team.short_name, dt.get_position_display())
                for dt in self.debateteam_set.all()])

    # --------------------------------------------------------------------------
    # Team properties
    # --------------------------------------------------------------------------
    # Team properties are stored in the dict `self._team_properties`, except for
    # the list of all teams, which is in `self._teams`. These are lazily
    # evaluated: on the first call of any team property,
    # `self._populate_teams()` is run to populate all team properties in a
    # single database query, then the appropriate value is returned.
    #
    # If the team in question doesn't exist or there is more than one, the
    # property in question will raise an ObjectDoesNotExist or
    # MultipleObjectsReturned exception, so that it behaves like a database
    # query. This exception raising is lazy: it does so only when the errant
    # property is called, rather than raising straight away in
    # `self._populate_teams()`.
    #
    # Callers that wish to retrieve the teams of many debates should add
    #   prefetch_related(Prefetch('debateteam_set', queryset=DebateTeam.objects.select_related('team'))
    # to their query set.

    def _populate_teams(self):
        """Populates the team attributes from self.debateteam_set."""
        dts = self.debateteam_set.all()
        if not dts._prefetch_done:  # uses internal undocumented flag of Django's QuerySet model
            dts = dts.select_related('team')

        self._teams = []
        self._multiple_found = []
        self._team_properties = {}

        for dt in dts:
            self._teams.append(dt.team)
            if dt.position == DebateTeam.POSITION_AFFIRMATIVE:
                if 'aff_team' in self._team_properties:
                    self._multiple_found.extend(['aff_team', 'aff_dt'])
                self._team_properties['aff_team'] = dt.team
                self._team_properties['aff_dt'] = dt
            elif dt.position == DebateTeam.POSITION_NEGATIVE:
                if 'neg_team' in self._team_properties:
                    self._multiple_found.extend(['neg_team', 'neg_dt'])
                self._team_properties['neg_team'] = dt.team
                self._team_properties['neg_dt'] = dt

    def _team_property(attr):  # noqa: N805
        """Used to construct properties that rely on self._populate_teams()."""
        @property
        def _property(self):
            if not hasattr(self, '_team_properties'):
                self._populate_teams()
            if attr in self._multiple_found:
                raise MultipleObjectsReturned("Multiple objects found for attribute '%s' in debate ID %d. "
                        "Teams in debate are: %s." % (attr, self.id, self._teams_and_positions_display()))
            try:
                return self._team_properties[attr]
            except KeyError:
                raise ObjectDoesNotExist("No object found for attribute '%s' in debate ID %d. "
                        "Teams in debate are: %s." % (attr, self.id, self._teams_and_positions_display()))
        return _property

    @property
    def teams(self):
        # No need for _team_property overhead, this list is guaranteed to exist
        # (it just might be empty).
        if not hasattr(self, '_teams'):
            self._populate_teams()
        return self._teams

    aff_team = _team_property('aff_team')
    neg_team = _team_property('neg_team')
    aff_dt = _team_property('aff_dt')
    neg_dt = _team_property('neg_dt')

    def get_team(self, side):
        return getattr(self, '%s_team' % side)

    def get_dt(self, side):
        """dt = DebateTeam"""
        return getattr(self, '%s_dt' % side)

    # --------------------------------------------------------------------------
    # Other properties
    # --------------------------------------------------------------------------

    @property
    def confirmed_ballot(self):
        """Returns the confirmed BallotSubmission for this debate, or None if
        there is no such ballot submission."""
        try:
            return self._confirmed_ballot
        except AttributeError:
            try:
                self._confirmed_ballot = self.ballotsubmission_set.get(confirmed=True)
            except ObjectDoesNotExist:
                self._confirmed_ballot = None
            return self._confirmed_ballot

    def get_flags_display(self):
        if not self.flags:
            return []  # don't return [""]
        else:
            # If the verbose description can't be found, just show the raw flag
            return [DRAW_FLAG_DESCRIPTIONS.get(f, f) for f in self.flags.split(",")]

    @property
    def history(self):
        try:
            return self._history
        except AttributeError:
            self._history = self.aff_team.seen(self.neg_team, before_round=self.round.seq)
            return self._history

    @property
    def adjudicators(self):
        """Returns an AdjudicatorAllocation containing the adjudicators for this
        debate."""
        try:
            return self._adjudicators
        except AttributeError:
            from adjallocation.allocation import AdjudicatorAllocation
            self._adjudicators = AdjudicatorAllocation(self, from_db=True)
            return self._adjudicators

    @property
    def division_motion(self):
        from motions.models import Motion
        try:
            # Pretty sure there should never be > 1
            return Motion.objects.filter(round=self.round, divisions=self.division).first()
        except ObjectDoesNotExist:
            # It's easiest to assume a division motion is always present, so
            # return a fake one if it is not
            return Motion(text='-', reference='-')


class DebateTeamManager(models.Manager):
    use_for_related_fields = True

    def get_queryset(self):
        return super().get_queryset().select_related('debate')


class DebateTeam(models.Model):
    POSITION_AFFIRMATIVE = 'A'
    POSITION_NEGATIVE = 'N'
    POSITION_UNALLOCATED = 'u'
    POSITION_CHOICES = ((POSITION_AFFIRMATIVE, 'affirmative'),
                        (POSITION_NEGATIVE, 'negative'),
                        (POSITION_UNALLOCATED, 'unallocated'), )

    objects = DebateTeamManager()

    debate = models.ForeignKey(Debate, models.CASCADE, db_index=True)
    team = models.ForeignKey('participants.Team', models.PROTECT)
    position = models.CharField(max_length=1, choices=POSITION_CHOICES)

    def __str__(self):
        return '{} in {}'.format(self.team.short_name, self.debate)

    @property
    def opponent(self):
        try:
            return self._opponent
        except AttributeError:
            try:
                self._opponent = DebateTeam.objects.exclude(position=self.position).select_related(
                        'team', 'team__institution').get(debate=self.debate)
            except (DebateTeam.DoesNotExist, DebateTeam.MultipleObjectsReturned):
                logger.warning("No opponent found for %s", str(self))
                self._opponent = None
            return self._opponent

    def get_result_display(self):
        if self.win is True:
            return 'won'
        elif self.win is False:
            return 'lost'
        else:
            return 'result unknown'

    @property
    def win(self):
        """Convenience function. Returns True if this team won, False if this
        team lost, or None if there isn't a confirmed result.

        This result is stored for the lifetime of the instance -- it won't
        update on the same instance if a result is entered."""
        try:
            return self._win
        except AttributeError:
            try:
                self._win = self.teamscore_set.get(ballot_submission__confirmed=True).win
            except ObjectDoesNotExist:
                self._win = None
            return self._win

    def get_position_name(self, tournament=None):
        """Should be used instead of get_position_display() on views.
        `tournament` can be passed in if known, for performance."""
        if self.position == DebateTeam.POSITION_AFFIRMATIVE:
            return get_position_name(tournament or self.debate.round.tournament, 'aff', 'full')
        elif self.position == DebateTeam.POSITION_NEGATIVE:
            return get_position_name(tournament or self.debate.round.tournament, 'neg', 'full')
        else:
            return self.get_position_display()


class TeamPositionAllocation(models.Model):
    """Model to store team position allocations for tournaments like Joynt
    Scroll (New Zealand). Each team-round combination should have one of these.
    In tournaments without team position allocations, just don't use this
    model."""

    POSITION_AFFIRMATIVE = DebateTeam.POSITION_AFFIRMATIVE
    POSITION_NEGATIVE = DebateTeam.POSITION_NEGATIVE
    POSITION_UNALLOCATED = DebateTeam.POSITION_UNALLOCATED
    POSITION_CHOICES = DebateTeam.POSITION_CHOICES

    round = models.ForeignKey('tournaments.Round', models.CASCADE)
    team = models.ForeignKey('participants.Team', models.CASCADE)
    position = models.CharField(max_length=1, choices=POSITION_CHOICES)

    class Meta:
        unique_together = [('round', 'team')]

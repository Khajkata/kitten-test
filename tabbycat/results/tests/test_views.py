from utils.tests import ConditionalTableViewTest, TestCase

from tournaments.models import Round


class PublicResultsForRoundViewTestCase(ConditionalTableViewTest, TestCase):

    view_toggle = 'public_features__public_results'
    view_name = 'results-public-round'
    round_seq = 3

    def table_data(self):
        # Check number of debates is correct
        round = Round.objects.get(tournament=self.t, seq=self.round_seq)
        return round.debate_set.all().count() * 2

<template>

  <nav
    v-on:dragover.prevent
    v-on:dragenter="dragEnter"
    v-on:dragleave="dragLeave"
    v-on:drop="drop"
    v-bind:class="{ 'vue-is-drag-enter': isDroppable }"
    class="navbar navbar-default navbar-fixed-bottom vue-droppable unallocated-adjs">

    <debate-adjudicator v-if="roundInfo.roundIsPrelim"
      v-for="adj in adjudicators | orderBy 'score' -1"
      :adjorteam="adj">
    </debate-adjudicator>
    <debate-adjudicator v-if="!roundInfo.roundIsPrelim"
      v-for="adj in adjudicators | orderBy 'name'"
      :adjorteam="adj">
    </debate-adjudicator>

  </nav>

</template>

<script>
import DebateAdjudicator from './DebateAdjudicator.vue'
import DroppableMixin from '../mixins/DroppableMixin.vue'

export default {
  mixins: [DroppableMixin],
  props: {
    adjudicators: Array,
    roundInfo: Object
  },
  components: {
    'DebateAdjudicator': DebateAdjudicator
  },
  methods: {
    handleDrop: function(ev) {
      this.$dispatch('set-adj-unused');
    }
  }
}
</script>
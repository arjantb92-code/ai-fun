import { ref, computed } from 'vue'

export function useSelection() {
  const selected = ref(new Set<number | string>())

  const toggle = (id: number | string | null) => {
    if (id == null) return
    const s = new Set(selected.value)
    if (s.has(id)) {
      s.delete(id)
    } else {
      s.add(id)
    }
    selected.value = s
  }

  const selectAll = (ids: (number | string | null)[]) => {
    selected.value = new Set(ids.filter((id): id is number | string => id != null))
  }

  const clear = () => {
    selected.value = new Set()
  }

  const isSelected = (id: number | string | null) => id != null && selected.value.has(id)

  const getSelectedArray = () => Array.from(selected.value)

  const count = computed(() => selected.value.size)
  const hasSelection = computed(() => selected.value.size > 0)

  return {
    selected,
    toggle,
    selectAll,
    clear,
    isSelected,
    getSelectedArray,
    count,
    hasSelection
  }
}

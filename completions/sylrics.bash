_sylrics() {
  local cur="${COMP_WORDS[COMP_CWORD]}" prev="${COMP_WORDS[COMP_CWORD-1]}"
  case "$prev" in
    --source) COMPREPLY=( $(compgen -W 'native auto spicy' -- "$cur") ) ;;
    theme) COMPREPLY=( $(compgen -W 'warm purple mono ocean dynamic' -- "$cur") ) ;;
    typing) COMPREPLY=( $(compgen -W 'smooth words-beta' -- "$cur") ) ;;
    highlight) COMPREPLY=( $(compgen -W 'off bold-beta' -- "$cur") ) ;;
    preset) COMPREPLY=( $(compgen -W 'list minimal studio cinema' -- "$cur") ) ;;
    reading) COMPREPLY=( $(compgen -W 'dynamic fixed rolling' -- "$cur") ) ;;
    config) COMPREPLY=( $(compgen -W 'path list get set edit restore' -- "$cur") ) ;;
    cache) COMPREPLY=( $(compgen -W 'info clear' -- "$cur") ) ;;
    bridge) COMPREPLY=( $(compgen -W 'install status' -- "$cur") ) ;;
    *) COMPREPLY=( $(compgen -W 'play demo config theme preset reading typing highlight font source visualizer control doctor cache bridge --source --config --version --help' -- "$cur") ) ;;
  esac
}
complete -F _sylrics sylrics slyrics


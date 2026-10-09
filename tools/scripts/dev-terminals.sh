#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly WORKSPACE_ROOT="$(cd -- "${SCRIPT_DIR}/../.." && pwd)"
readonly SESSION_NAME='shinobi-showdown-dev'
readonly TAB_NAME='Shinobi Showdown'
readonly SERVER_PANE_NAME='Server'
readonly WEB_PANE_NAME='Web'
readonly SERVER_TARGET='game-server:serve'
readonly WEB_TARGET='web:serve'
readonly SERVER_COMMAND="npm exec nx run ${SERVER_TARGET}"
readonly WEB_COMMAND="npm exec nx run ${WEB_TARGET}"
readonly SESSION_LAYOUT='
layout {
    tab name="Shinobi Showdown" {
        pane split_direction="vertical" {
            pane name="Server" command="npm" {
                args "exec" "nx" "run" "game-server:serve"
            }
            pane name="Web" command="npm" {
                args "exec" "nx" "run" "web:serve"
            }
        }
    }
}'

if ! command -v npm >/dev/null 2>&1; then
  printf 'Error: npm is required but was not found in PATH.\n' >&2
  exit 1
fi

if ! command -v node >/dev/null 2>&1; then
  printf 'Error: Node.js is required to inspect the Zellij session.\n' >&2
  exit 1
fi

if ! command -v zellij >/dev/null 2>&1; then
  printf 'Error: Zellij is required to run both services in one terminal tab.\n' >&2
  exit 1
fi

if command -v ghostty >/dev/null 2>&1; then
  readonly TERMINAL_EMULATOR='ghostty'
elif command -v xterm >/dev/null 2>&1; then
  readonly TERMINAL_EMULATOR='xterm'
else
  printf 'Error: install Ghostty or xterm to launch the development services.\n' >&2
  exit 1
fi

session_exists() {
  zellij list-sessions --short --no-formatting 2>/dev/null | grep -Fxq "${SESSION_NAME}"
}

pane_is_running() {
  local panes_json="$1"
  local title="$2"
  local expected_command="$3"

  node -e '
const fs = require("node:fs");
const [title, expectedCommand] = process.argv.slice(1);
const panes = JSON.parse(fs.readFileSync(0, "utf8"));
const isRunning = panes.some(
  (pane) =>
    !pane.is_plugin &&
    pane.title === title &&
    pane.exited === false &&
    pane.pane_command === expectedCommand,
);
process.exit(isRunning ? 0 : 1);
' "${title}" "${expected_command}" <<<"${panes_json}"
}

pane_tab_id() {
  local panes_json="$1"
  local title="$2"
  local expected_command="$3"

  node -e '
const fs = require("node:fs");
const [title, expectedCommand] = process.argv.slice(1);
const panes = JSON.parse(fs.readFileSync(0, "utf8"));
const pane = panes.find(
  (candidate) =>
    !candidate.is_plugin &&
    candidate.title === title &&
    candidate.exited === false &&
    candidate.pane_command === expectedCommand,
);
if (!pane) process.exit(1);
process.stdout.write(String(pane.tab_id));
' "${title}" "${expected_command}" <<<"${panes_json}"
}

named_tab_id() {
  local panes_json="$1"

  node -e '
const fs = require("node:fs");
const tabName = process.argv[1];
const panes = JSON.parse(fs.readFileSync(0, "utf8"));
const pane = panes.find(
  (candidate) => !candidate.is_plugin && candidate.tab_name === tabName,
);
if (!pane) process.exit(1);
process.stdout.write(String(pane.tab_id));
' "${TAB_NAME}" <<<"${panes_json}"
}

stale_pane_ids() {
  local panes_json="$1"
  local title="$2"

  node -e '
const fs = require("node:fs");
const title = process.argv[1];
const panes = JSON.parse(fs.readFileSync(0, "utf8"));
for (const pane of panes) {
  if (!pane.is_plugin && pane.title === title && pane.exited === true) {
    process.stdout.write(`terminal_${pane.id}\n`);
  }
}
' "${title}" <<<"${panes_json}"
}

start_pane() {
  local tab_id="$1"
  local title="$2"
  local target="$3"

  zellij --session "${SESSION_NAME}" action new-pane \
    --tab-id "${tab_id}" \
    --direction right \
    --name "${title}" \
    --cwd "${WORKSPACE_ROOT}" \
    -- npm exec nx run "${target}" >/dev/null
}

close_stale_panes() {
  local panes_json="$1"
  local title="$2"
  local pane_id

  while IFS= read -r pane_id; do
    if [[ -n "${pane_id}" ]]; then
      zellij --session "${SESSION_NAME}" action close-pane --pane-id "${pane_id}" >/dev/null
    fi
  done < <(stale_pane_ids "${panes_json}" "${title}")
}

ensure_services_are_running() {
  local panes_json
  local server_running='false'
  local web_running='false'
  local tab_id=''

  panes_json="$(zellij --session "${SESSION_NAME}" action list-panes --all --json)"

  if pane_is_running "${panes_json}" "${SERVER_PANE_NAME}" "${SERVER_COMMAND}"; then
    server_running='true'
    tab_id="$(pane_tab_id "${panes_json}" "${SERVER_PANE_NAME}" "${SERVER_COMMAND}")"
  fi

  if pane_is_running "${panes_json}" "${WEB_PANE_NAME}" "${WEB_COMMAND}"; then
    web_running='true'
    if [[ -z "${tab_id}" ]]; then
      tab_id="$(pane_tab_id "${panes_json}" "${WEB_PANE_NAME}" "${WEB_COMMAND}")"
    fi
  fi

  if [[ -z "${tab_id}" ]]; then
    tab_id="$(named_tab_id "${panes_json}" || true)"
  fi

  if [[ -z "${tab_id}" ]]; then
    zellij --session "${SESSION_NAME}" action new-tab \
      --layout-string "${SESSION_LAYOUT}" >/dev/null
    server_running='true'
    web_running='true'
  elif [[ "${server_running}" == 'false' ]]; then
    start_pane "${tab_id}" "${SERVER_PANE_NAME}" "${SERVER_TARGET}"
  fi

  if [[ "${web_running}" == 'false' ]]; then
    start_pane "${tab_id}" "${WEB_PANE_NAME}" "${WEB_TARGET}"
  fi

  close_stale_panes "${panes_json}" "${SERVER_PANE_NAME}"
  close_stale_panes "${panes_json}" "${WEB_PANE_NAME}"
}

build_zellij_command() {
  if session_exists; then
    ensure_services_are_running
    printf 'cd %q && exec zellij attach %q' "${WORKSPACE_ROOT}" "${SESSION_NAME}"
  else
    printf \
      'cd %q && exec zellij --layout-string %q options --session-name %q --session-serialization false' \
      "${WORKSPACE_ROOT}" \
      "${SESSION_LAYOUT}" \
      "${SESSION_NAME}"
  fi
}

launch_terminal() {
  local command

  command="$(build_zellij_command)"

  case "${TERMINAL_EMULATOR}" in
    ghostty)
      ghostty \
        --title="${TAB_NAME}" \
        --wait-after-command=true \
        -e bash -lc "${command}" &
      ;;
    xterm)
      xterm \
        -hold \
        -T "${TAB_NAME}" \
        -e bash -lc "${command}" &
      ;;
  esac
}

main() {
  launch_terminal

  printf \
    'Opened Zellij session %s with the server and web application in one %s window.\n' \
    "${SESSION_NAME}" \
    "${TERMINAL_EMULATOR}"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main
fi

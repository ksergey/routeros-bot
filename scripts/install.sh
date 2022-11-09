#!/bin/bash

SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
RO_PATH="$( cd "${SCRIPT_PATH}/.." >/dev/null 2>&1; pwd -P )"
RO_ENV="${RO_VENV:-${HOME}/routeros-bot-env}"
RO_CONFIG_PATH="${HOME}/routeros-bot.conf"

Red='\033[0;31m'
Green='\033[0;32m'
Cyan='\033[0;36m'
Normal='\033[0m'

echo_text()
{
  printf "${Normal}$1${Cyan}\n"
}

echo_error()
{
  printf "${Red}$1${Normal}\n"
}

echo_ok()
{
  printf "${Green}$1${Normal}\n"
}

install_packages()
{
  python3 -m pip install --upgrade pip
  if [ $? -eq 0 ]; then
    echo_ok "Installed pip"
  else
    echo_error "Installation of pip failed"
  fi

  pip3 install virtualenv
  if [ $? -eq 0 ]; then
    echo_ok "Installed virtualenv"
  else
    echo_error "Installation of virtualenv failed"
  fi
}

create_virtualenv()
{
  echo_text "Creating virtual environment"
  if [ ! -d ${RO_ENV} ]; then
    virtualenv -p /usr/bin/python3 ${RO_ENV}
  fi

  source ${RO_ENV}/bin/activate
  while read requirements; do
    pip --disable-pip-version-check install $requirements
    if [ $? -gt 0 ]; then
    	echo "Error: pip install exited with status code $?"
      echo "Unable to install dependencies, aborting install."
      deactivate
      exit 1
    fi
  done < ${RO_PATH}/requirements.txt
  deactivate
  echo_ok "Virtual enviroment created"
}

create_default_config()
{
  echo_text "Create default config"
  if [ ! -f "${RO_CONFIG_PATH}" ]; then
    cp ${RO_PATH}/routeros-bot.conf ${RO_CONFIG_PATH}
    echo "Default config created (${RO_CONFIG_PATH})"
  else
    echo "Config already exists (${RO_CONFIG_PATH})"
  fi
}

install_systemd_service()
{
  echo_text "Installing routeros-bot unit file"

  mkdir -p ${HOME}/.config/systemd/user

cat > ${HOME}/.config/systemd/user/routeros-bot.service <<EOF
[Unit]
Description=routeros bot for Telegram
After=network.target

[Service]
WorkingDirectory=${RO_PATH}
ExecStart=${RO_ENV}/bin/python3 -m app --config ${RO_CONFIG_PATH}

[Install]
WantedBy=default.target
EOF

  systemctl --user unmask routeros-bot.service
  systemctl --user daemon-reload
  systemctl --user enable routeros-bot.service
}

start_systemd_service()
{
  systemctl --user start routeros-bot.service
}

install_packages
create_virtualenv
create_default_config
install_systemd_service
echo_ok "routeros bot was installed"
start_systemd_service

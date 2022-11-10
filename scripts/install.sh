#!/bin/bash

SCRIPT_PATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
ROOT_PATH="$( cd "${SCRIPT_PATH}/.." >/dev/null 2>&1; pwd -P )"
ENV_PATH="${HOME}/routeros-bot-env"
CONFIG_SRC_PATH="${ROOT_PATH}/routeros-bot.conf"
CONFIG_PATH="${HOME}/routeros-bot.conf"
SERVICE_NAME="routeros-bot.service"
SERVICE_DESCRIPTION="RouterOS bot for Telegram"

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
  if [ ! -d ${ENV_PATH} ]; then
    virtualenv -p /usr/bin/python3 --system-site-packages ${ENV_PATH}
  fi

  source ${ENV_PATH}/bin/activate
  while read requirements; do
    pip --disable-pip-version-check --no-cache-dir install $requirements
    if [ $? -gt 0 ]; then
    	echo "Error: pip install exited with status code $?"
      echo "Unable to install dependencies, aborting install."
      deactivate
      exit 1
    fi
  done < ${ROOT_PATH}/requirements.txt
  deactivate
  echo_ok "Virtual enviroment created"
}

create_default_config()
{
  echo_text "Create default config"
  if [ ! -f "${CONFIG_PATH}" ]; then
    cp "${CONFIG_SRC_PATH}" "${CONFIG_PATH}"
    echo "Default config created (${CONFIG_PATH})"
  else
    echo "Config already exists (${CONFIG_PATH})"
  fi
}

install_systemd_service()
{
  echo_text "Installing systemd unit file"

  mkdir -p ${HOME}/.config/systemd/user

cat > ${HOME}/.config/systemd/user/${SERVICE_NAME} <<EOF
[Unit]
Description=${SERVICE_DESCRIPTION}
After=network.target

[Service]
Type=simple
WorkingDirectory=${ROOT_PATH}
ExecStart=${ENV_PATH}/bin/python3 -m app --config ${CONFIG_PATH}
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
EOF

  systemctl --user unmask ${SERVICE_NAME}
  systemctl --user daemon-reload
  systemctl --user enable ${SERVICE_NAME}
}

start_systemd_service()
{
  systemctl --user start ${SERVICE_NAME}
}

install_packages
create_virtualenv
create_default_config
install_systemd_service
echo_ok "Bot was installed"
start_systemd_service

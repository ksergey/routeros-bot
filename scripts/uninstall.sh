#!/bin/bash

echo "Uninstalling routeros-bot"
echo ""
echo "* Stopping service"
systemctl --user stop routeros-bot.service
echo "* Removing unit file"
rm ${HOME}/.config/systemd/user/routeros-bot.service
echo "* Removing enviroment"
rm -rf ${HOME}/routeros-bot-env
echo "Done"

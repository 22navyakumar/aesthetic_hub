#!/usr/bin/env bash
# =============================================================================
# install_emulation_cron.sh — Installs the production data emulation cron job
#
# Run this on node1 after setup:
#   bash aesthetic/pipelines/batch/install_emulation_cron.sh
#
# This adds a cron entry that runs emulate_production.sh every 6 hours
# (00:00, 06:00, 12:00, 18:00 UTC) from Wednesday through Sunday.
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EMULATE_SCRIPT="$SCRIPT_DIR/emulate_production.sh"

chmod +x "$EMULATE_SCRIPT"

# Remove any existing emulate_production cron entries
crontab -l 2>/dev/null | grep -v "emulate_production" > /tmp/crontab_clean || true

# Add new cron: every 6 hours (00, 06, 12, 18), Wednesday(3) through Sunday(0)
# Cron day-of-week: 0=Sun, 3=Wed, 4=Thu, 5=Fri, 6=Sat
echo "0 0,6,12,18 * * 0,3,4,5,6 $EMULATE_SCRIPT >> /tmp/emulate-production-logs/cron.log 2>&1" >> /tmp/crontab_clean

# Install
crontab /tmp/crontab_clean
rm /tmp/crontab_clean

echo "Cron installed. Current crontab:"
crontab -l

echo ""
echo "To run setup (create users + API keys), run:"
echo "  $EMULATE_SCRIPT --setup"
echo ""
echo "To test a single batch manually:"
echo "  $EMULATE_SCRIPT"

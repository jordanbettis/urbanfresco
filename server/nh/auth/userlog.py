from nh.core.config import CONFIG

from datetime import datetime

import json

LOG_FD = open("%s/user.log" % CONFIG.LOG_DIR, "a")

def log(event, user, data):
    """
    event: A string that identifies the event being recorded
    user: An nh.auth.user object
    data: a serializable structure containing whatever additional data is relevant
    """
    line = [datetime.now().isoformat(), event, user.id, data]
    LOG_FD.write(json.dumps(line) + "\n")

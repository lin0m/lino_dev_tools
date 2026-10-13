from lino_dev_tools.logs import *

log = Log()
# write to log
# log.write(DEBUG, "Debug message")
# log.write(INFO, "Info message")
# log.write(ERROR, "Error message")

# log.new_session()
# log.write(CRITICAL, "Critical message",12)
# log.write(CRITICAL, "Critical message",12)
# log.write(CRITICAL, "Critical message",12)

# read log
log_events = log.read()
log_events.print()
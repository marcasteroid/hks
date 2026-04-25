# Inner attempt structure K2
nodes: send, wait, ack, timeout, ok, fail
boxes:
entry: send
exit: ok

label:
    send: # Set "send: ack" to get Result = True
    wait:
    ack: ack
    timeout: timeout
    ok: ok
    fail: fail

map:

edges:
    send -> wait
    wait -> ack
    wait -> timeout
    ack -> ok
    timeout -> fail
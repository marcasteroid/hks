# Inner attempt structure K2
nodes: send, wait, ack, timeout, ok, fail
boxes:
entry: send
exit: ok

label:
    send:
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
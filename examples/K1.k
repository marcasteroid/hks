# Top‑level structure K1
nodes: start, abort, success
boxes: try1, try2
entry: start
exit: success

label:
    start: start
    abort: abort
    success: success

map:
    try1: 2
    try2: 2

edges:
    start -> try1
    (try1, fail) -> try2
    (try2, fail) -> abort
    (try1, ok) -> success
    (try2, ok) -> success
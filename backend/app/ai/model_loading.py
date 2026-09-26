"""One process-wide lock for importing and loading the local ML models.

The embedding model (sentence-transformers) and the NER model both import
`transformers`, whose package initialises lazily. When the NER model loads
in its startup background thread while the first chat request loads the
embedding model, the two threads can see `transformers` half-initialised:
    ImportError: cannot import name 'AutoConfig' from 'transformers'
(seen live as a 500 on the first chat message after a restart). Holding
this lock around both loads makes them take turns; the second simply waits.
"""

import threading

MODEL_LOAD_LOCK = threading.Lock()

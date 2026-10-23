import inspect

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


def _accepts_progress(fn):
    try:
        return "progress" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


class _WorkerSignals(QObject):
    done = Signal(object)
    error = Signal(str)
    progress = Signal(object)


class _Worker(QRunnable):
    def __init__(self, fn, args, kwargs):
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._reports_progress = _accepts_progress(fn)
        self.signals = _WorkerSignals()

    def run(self):
        try:
            if self._reports_progress:
                result = self._fn(
                    *self._args, progress=self.signals.progress.emit, **self._kwargs
                )
            else:
                result = self._fn(*self._args, **self._kwargs)
        except Exception as exc:  # noqa: BLE001 - 统一转成界面提示
            self.signals.error.emit(str(exc))
        else:
            self.signals.done.emit(result)


class TaskRunner(QObject):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pool = QThreadPool.globalInstance()
        self._active = set()

    def submit(self, fn, *args, on_done=None, on_error=None, on_progress=None, **kwargs):
        worker = _Worker(fn, args, kwargs)
        self._active.add(worker)
        worker.signals.done.connect(lambda result, w=worker: self._complete(w, on_done, result))
        worker.signals.error.connect(lambda message, w=worker: self._complete(w, on_error, message))
        if on_progress is not None:
            worker.signals.progress.connect(on_progress)
        self._pool.start(worker)
        return worker

    def _complete(self, worker, callback, payload):
        self._active.discard(worker)
        if callback is not None:
            callback(payload)

class Worker(object):
    def __init__(self):
        self._exit_codes = None
        self._exit_status = None

    def __call__(self):
        try:
            self.runner()
        except Exception as e:
            raise e

    def setup(self):
        pass

    def teardown(self):
        pass

    def runner(self):
        raise NotImplementedError()

    def get_exit_codes(self):
        return self._exit_codes

    def get_exit_status(self):
        return self._exit_status

    def debug(self):
        pass

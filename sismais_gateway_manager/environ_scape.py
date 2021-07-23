from environ import Env
from environ.environ import NoValue

class EnvScape(Env):
    NOTSET = NoValue()

    def str(self, var, default=NOTSET, multiline=False, escape=False):
        """
        :rtype: str
        """
        value = self.get_value(var, cast=str, default=default)
        if multiline:
            return value.replace('\\n', '\n')
        if escape:
            return value.replace('\$', '$')
        return value
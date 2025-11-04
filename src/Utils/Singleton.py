class Singleton(type):
    """
    Implémentation simple du design pattern Singleton avec métaclasse.
    Garantit qu'une seule instance d'une classe existe à la fois.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

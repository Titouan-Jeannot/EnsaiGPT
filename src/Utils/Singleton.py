class Singleton(type):
    """
    Implémentation simple du design pattern Singleton avec métaclasse.
    Garantit qu'une seule instance d'une classe existe à la fois.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Crée une instance unique de la classe si elle n'existe pas encore, sinon retourne l'instance existante."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

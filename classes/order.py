class Order:
    def __init__(self, ordernummer, totaalprijs, betaald, oliebollen, appelbeignets, naam, ophalen_of_bezorgen, datum, tijd, factuuradres, leveradres, factuurpostcode, leverpostcode, factuurplaats, leverplaats, telefoonnummer, bezorgkosten, gift):
        self.ordernummer = ordernummer
        self.totaalprijs = totaalprijs
        self.betaald = betaald
        self.oliebollen = oliebollen
        self.appelbeignets = appelbeignets
        self.naam = naam
        self.ophalen_of_bezorgen = ophalen_of_bezorgen
        self.datum = datum
        self.tijd = tijd
        self.factuuradres = factuuradres
        self.leveradres = leveradres
        self.factuurpostcode = factuurpostcode
        self.leverpostcode = leverpostcode
        self.factuurplaats = factuurplaats
        self.leverplaats = leverplaats
        self.telefoonnummer = telefoonnummer
        self.bezorgkosten = bezorgkosten
        self.gift = gift

    def __str__(self):
        return f"Order #{self.ordernummer} - {self.naam}\nTotal Price: €{self.totaalprijs}\nPaid: {self.betaald}\nOliebollen: {self.oliebollen}, Appelbeignets: {self.appelbeignets}\nPickup/Delivery: {self.ophalen_of_bezorgen}\nDate: {self.datum} {self.tijd}\nInvoice Address: {self.factuuradres} {self.factuurpostcode} {self.factuurplaats}\nDelivery Address: {self.leveradres} {self.leverpostcode} {self.leverplaats}\nPhone: {self.telefoonnummer}\nDelivery Cost: €{self.bezorgkosten}\nGift: {self.gift}"

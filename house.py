import random as rnd


class Household(object):
    def __init__(self, id, address, ruler):
        self.id = id
        self.pv = None
        self.address = address  # aka public key - address, wallet
        self.ruler = ruler  # rulerAgent
        self.status = None

        self.loyalty = 1.0  # used for DA price formation

    def getBasicInfo(self):
        return "Household id is {0}, RA: {1}, \
                address in Ethereum blockchain:{2}".format(
            self.id, self.ruler.id, self.address
        )

    def checkPV(self):
        if self.pv:
            return True
        else:
            return False

    def getHomeProbStatus(self, hour):
        # True - at home, False - away
        rnd.seed()
        actual_prob = rnd.random()
        fun_prob = [
            0.92,
            0.891,
            0.859,
            0.823,
            0.784,
            0.741,
            0.696,
            0.649,
            0.6,
            0.5,
            0.55,
            0.599,
            0.646,
            0.691,
            0.734,
            0.773,
            0.809,
            0.841,
            0.87,
            0.894,
            0.92,
            0.9,
            0.9,
            0.96,
        ]

        if actual_prob > fun_prob[hour]:
            state = False
        else:
            state = True

        self.ruler.homeStatus = state

        return state


class RulerAgent(object):
    def __init__(self, id, batteryCap):
        self.id = id
        self.batteryCap = batteryCap
        self.batteryBalance = 0

        self.tokenBalance = 0
        self.moneyBalance = 0

        self.consumption = 0

        self.production = 0
        self.pvSq = None

        self.homeStatus = None

        self.avgConsRateList = []

    def getLastHourProduction(self, currentHour, weather):
        # production for prev hour (23-0)
        rnd.seed()
        if currentHour > 5 and currentHour < 21:
            if self.pvSq > 0:
                val = self.pvSq * weather[1][1] * rnd.randint(1, 11)
                return 100 * int(val)
            else:
                return 0
        else:
            return 0

    def getNextHourConsumption(self, currentHour, weather):
        # consumption for next hour (0-1)
        status = self.homeStatus
        rnd.seed()
        if status:
            if currentHour > 7 and currentHour < 23:
                return int(rnd.randint(5, 20) * (weather[1][0])) * 100  # 1-20
            else:
                return int(rnd.randint(2, 8) * weather[1][0]) * 100  # 1-20
        else:
            return int(rnd.randint(0, 5) * weather[1][0]) * 100  # 0-5

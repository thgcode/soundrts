from lib.nofloat import square_of_distance


class Action:
    
    def __init__(self, unit, target):
        self.unit = unit
        self.target = target

    def complete(self):
        self.unit.walked = []
        self.unit.action = None

    def update(self):
        pass


class MoveAction(Action):
    
    def update(self):
        if hasattr(self.target, "other_side"):
            # move towards the center of the next square
            self.unit.go_to_xy(self.target.other_side.place.x, self.target.other_side.place.y)
        elif getattr(self.target, "place", None) is self.unit.place:
            self.unit.action_reach_and_stop()
        elif self.unit.airground_type == "air":
            self.unit.go_to_xy(self.target.x, self.target.y)
        else:
            self.complete()


class MoveXYAction(Action):

    def update(self):
        x, y = self.target
        u = self.unit
        subsquare = u.world.get_subsquare_id_from_xy
        d2 = square_of_distance(x, y, u.x, u.y)
        if subsquare(x, y) != subsquare(u.x, u.y):
            if u.go_to_xy(x, y):
                self.complete()
        else:
            # try as long as the distance is decreasing
            previous_d2 = square_of_distance(x, y, u.x, u.y)
            if u.go_to_xy(x, y) or square_of_distance(x, y, u.x, u.y) > previous_d2:
                self.complete()


class AttackAction(Action):

    def update(self): # without moving to another square
        if self.unit.range and self.target in self.unit.place.objects:
            self.unit.action_reach_and_aim()
        elif self.unit.can_attack(self.target):
            self.unit.aim(self.target)
        else:
            self.complete()

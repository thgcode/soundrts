import unittest

from soundrts.mapfile import Map
from soundrts.lib.nofloat import PRECISION
from soundrts.world import World
from soundrts import worldclient
from soundrts.worldorders import BuildOrder, TrainOrder
from soundrts.worldplayerbase import Objective 
from soundrts.worldresource import Corpse


def disable_ai(player):
    def do_nothing():
        pass
    player.play = do_nothing


class ObjectiveTestCase(unittest.TestCase):

    def testInit(self):
        o = Objective(1, [12, 13, 14])
        self.assertEqual(o.number, 1)
        self.assertEqual(o.description, [12, 13, 14])


class DummyClient(worldclient.DummyClient):

    def push(self, *args):
        if False: # remove this to check the values
            print(args)
 

class _PlayerBaseTestCase(unittest.TestCase):

    def set_up(self, alliance=(1, 2), cloak=False, map_name="jl1_extended"):
        self.w = World([])
        self.w.introduction = []
        self.w.load_and_build_map(Map("soundrts/tests/%s.txt" % map_name))
        if cloak:
            self.w.unit_class("new_flyingmachine").dct["is_a_cloaker"] = True
        self.w.populate_map([DummyClient(), DummyClient()], alliance)
        self.cp, self.cp2 = self.w.players

    def find_player_unit(self, p, cls_name, index=0):
        for u in p.units:
            if u.type_name == cls_name:
                if index:
                    index -= 1
                else:
                    return u


class PlayerBaseTestCase(_PlayerBaseTestCase):

    def testStorageBonus(self):
        self.set_up()
        self.w.update()
        assert sorted((self.cp.storage_bonus[1], self.cp2.storage_bonus[1])) == [0, 0]
        for _ in range(2):
            self.cp2.lang_add_units(["b4", "lumbermill"])
            self.w.update()
            assert sorted((self.cp.storage_bonus[1], self.cp2.storage_bonus[1])) == [0, 1 * PRECISION]

    def testNoCountLimit(self):
        self.set_up()
        disable_ai(self.cp)
        th = self.find_player_unit(self.cp, "townhall")
        th.take_order(["train", "peasant"])
        assert th.orders

    def testCountLimit(self):
        self.set_up()
        disable_ai(self.cp)
        self.w.unit_class("peasant").count_limit = 1
        self.w.update()
        th = self.find_player_unit(self.cp, "townhall")
        self.assertNotIn("train peasant", TrainOrder.menu(th))
        th.take_order(["train", "peasant"])
        assert not th.orders
        self.w.unit_class("peasant").count_limit = 2
        self.w.update()
        self.assertIn("train peasant", TrainOrder.menu(th))
        th.take_order(["train", "peasant"])
        assert th.orders
        
    def testCountLimitBuild(self):
        self.set_up()
        disable_ai(self.cp)
        self.cp.lang_add_units(["b2", "peasant"])
        self.cp.resources = [1000*PRECISION, 1000*PRECISION]
        self.w.unit_class("barracks").is_buildable_anywhere = True
        self.w.unit_class("barracks").count_limit = 1
        self.w.update()
        p1 = self.find_player_unit(self.cp, "peasant")
        p2 = self.find_player_unit(self.cp, "peasant", 1)
        self.assertEqual(p1.orders, [])
        self.assertEqual(p2.orders, [])
        self.assertIn("build barracks", BuildOrder.menu(p1))
        p1.take_order(["build", "barracks", "a2"])
        p2.take_order(["build", "barracks", "a2"])
        assert p1.orders
        assert p2.orders
        for _ in range(1000):
            self.w.update()
            if not (p1.orders or p2.orders):
                break
        self.assertEqual(p1.orders, [])
        self.assertEqual(p2.orders, [])
        self.assertEqual(self.cp.nb("barracks"), 1)
        self.assertNotIn("build barracks", BuildOrder.menu(p1))
        p1.take_order(["build", "barracks", "a2"])
        p2.take_order(["build", "barracks", "a2"])
        self.assertEqual(p1.orders, [])
        self.assertEqual(p2.orders, [])
        self.assertEqual(self.cp.nb("barracks"), 1)
        self.w.unit_class("barracks").count_limit = 2
        self.w.update()
        self.assertEqual(self.cp.future_count("barracks"), 1)
        p1.take_order(["build", "barracks", "a2"])
        p2.take_order(["build", "barracks", "a2"])
        self.assertEqual(self.cp.future_count("barracks"), 1)
        assert p1.orders[0].keyword == "build"
        assert p1.orders[0].type.type_name == "barracks"
        assert p2.orders[0].keyword == "build"
        for _ in range(1000):
            self.w.update()
            if not (p1.orders or p2.orders):
                break
        self.assertEqual(p1.orders, [])
        self.assertEqual(p2.orders, [])
        self.assertEqual(self.cp.future_count("barracks"), 2)
        self.assertEqual(self.cp.nb("barracks"), 2)
        self.assertEqual(self.cp.nb("farm"), 1)
        p1.take_order(["build", "farm", "a2"])
        for _ in range(1000):
            self.w.update()
            if not p1.orders:
                break
        self.assertEqual(self.cp.nb("farm"), 2)

    def testCountLimitBuildQueued(self):
        self.set_up()
        disable_ai(self.cp)
        self.cp.lang_add_units(["b2", "peasant"])
        self.cp.resources = [1000*PRECISION, 1000*PRECISION]
        self.w.unit_class("barracks").is_buildable_anywhere = True
        self.w.unit_class("barracks").count_limit = 1
        self.w.update()
        p1 = self.find_player_unit(self.cp, "peasant")
        p2 = self.find_player_unit(self.cp, "peasant", 1)
        self.assertEqual(p1.orders, [])
        self.assertEqual(p2.orders, [])
        p1.take_order(["build", "barracks", "a2"])
        p2.take_order(["build", "barracks", "a2"])
        p1.take_order(["build", "barracks", "a2"], forget_previous=False)
        p2.take_order(["build", "barracks", "a2"], forget_previous=False)
        assert len(p1.orders) == 2
        assert len(p2.orders) == 2
        for _ in range(1000):
            self.w.update()
            if not (p1.orders or p2.orders):
                break
        self.assertEqual(p1.orders, [])
        self.assertEqual(p2.orders, [])
        self.assertEqual(self.cp.nb("barracks"), 1)

    def testCountLimitUpgradeTo(self):
        self.set_up()
        disable_ai(self.cp)
        self.cp.lang_add_units(["b2", "lumbermill"])
        self.cp.lang_add_units(["b2", "magestower"])
        self.cp.lang_add_units(["b2", "archer"])
        self.cp.lang_add_units(["b2", "archer"])
        self.cp.resources = [1000*PRECISION, 1000*PRECISION]
        self.w.unit_class("darkarcher").count_limit = 1
        self.w.update()
        a1 = self.find_player_unit(self.cp, "archer")
        a2 = self.find_player_unit(self.cp, "archer", 1)
        a1.take_order(["upgrade_to", "darkarcher"])
        a2.take_order(["upgrade_to", "darkarcher"])
        self.assertEqual(a1.orders[0].keyword, "upgrade_to")
        self.assertEqual(a2.orders, [])
        
    def testCountLimitSummon(self):
        self.set_up()
        disable_ai(self.cp)
        self.assertEqual(self.cp.nb("dragon"), 1)
        self.w.unit_class("dragon").count_limit = 2
        self.cp.lang_add_units(["b2", "mage"])
        self.cp.upgrades.append("u_summon_dragon")
        self.w.update()
        m = self.find_player_unit(self.cp, "mage")
        m.take_order(["use", "a_summon_dragon", "b2"])
        self.w.update()
        self.assertEqual(self.cp.nb("dragon"), 2)

    def testCountLimitRaiseDead(self):
        self.set_up()
        disable_ai(self.cp)
        self.cp.lang_add_units(["b2", "10", "footman"])
        for _ in range(10):
            f = self.find_player_unit(self.cp, "footman")
            assert f.place.name == "b2"
            f.die()
        self.assertEqual(self.cp.nb("zombie"), 0)
        self.w.unit_class("zombie").count_limit = 1
        self.cp.lang_add_units(["b2", "necromancer"])
        self.cp.upgrades.append("u_raise_dead")
        self.w.update()
        n = self.find_player_unit(self.cp, "necromancer")
        n.take_order(["use", "a_raise_dead", "b2"])
        self.w.update()
        self.assertEqual(self.cp.nb("zombie"), 1)
        
    def testCountLimitResurrection(self):
        self.set_up()
        self.cp.resources = [1000*PRECISION, 1000*PRECISION]
        disable_ai(self.cp)
        self.cp.lang_add_units(["b2", "10", "footman"])
        for _ in range(10):
            f = self.find_player_unit(self.cp, "footman")
            assert f.place.name == "b2"
            f.die()
        self.assertEqual(self.cp.nb("footman"), 0)
        self.w.unit_class("footman").count_limit = 2
        self.w.update()
        self.w.update()
        self.cp.lang_add_units(["b2", "priest"])
        self.cp.upgrades.append("u_resurrection")
        p = self.find_player_unit(self.cp, "priest")
        p.take_order(["use", "a_resurrection", "b2"])
        self.w.update()
        self.assertEqual(self.cp.nb("footman"), 2)

    def testCountLimitResurrectionWithTrainQueue(self):
        self.set_up()
        self.cp.resources = [1000*PRECISION, 1000*PRECISION]
        disable_ai(self.cp)
        self.cp.lang_add_units(["b2", "10", "footman"])
        for _ in range(10):
            f = self.find_player_unit(self.cp, "footman")
            assert f.place.name == "b2"
            f.die()
        self.assertEqual(self.cp.nb("footman"), 0)
        self.w.unit_class("footman").count_limit = 2
        self.cp.lang_add_units(["b2", "barracks"])
        self.w.update()
        b = self.find_player_unit(self.cp, "barracks")
        b.take_order(["train", "footman"])
        self.w.update()
        self.cp.lang_add_units(["b2", "priest"])
        self.cp.upgrades.append("u_resurrection")
        p = self.find_player_unit(self.cp, "priest")
        p.take_order(["use", "a_resurrection", "b2"])
        self.w.update()
        self.assertEqual(self.cp.nb("footman"), 1)


class ComputerTestCase(_PlayerBaseTestCase):

    def testInitAndGetAPeasant(self):
        self.set_up()
        assert sorted(self.w.get_makers("peasant")) == ["castle", "keep", "townhall"]
        assert sorted(self.w.get_makers("footman")) == ["barracks"]
        assert sorted(self.w.get_makers("barracks")) == ["peasant"]
        th = self.find_player_unit(self.cp, "townhall")
        assert not th.orders
        assert not self.cp.get(1000, "peasant")
        assert th.orders

    def testInitAndGetAFootman(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        assert not p.orders
        assert not self.cp.get(1000, "footman")
        assert p.orders

    def testInitAndUpgradeToAKeep(self):
        self.set_up()
        self.cp.resources = [1000*PRECISION, 1000*PRECISION]
        th = self.find_player_unit(self.cp, "townhall")
        assert not th.orders
        assert not self.cp.get(1, "keep")
        assert not th.orders
        self.cp.lang_add_units(["a1", "barracks"])
        assert self.find_player_unit(self.cp, "barracks")
        assert not self.cp.get(1, "knight") # => get keep
        assert th.orders

    def testMenace(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        assert p.menace > 0
        th = self.find_player_unit(self.cp, "townhall")
        assert th.menace == 0

    def testImmediateOrder(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        p.take_order(["go", 1])
        assert p.orders
        p.take_order(["mode_offensive"])
        assert p.orders

    def testPerception(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        assert p.player.is_perceiving(p)
        p2 = self.find_player_unit(self.cp2, "peasant")
        p2place = p2.place
        assert not p.player.is_perceiving(p2)
        assert not p.place in p2.player.observed_before_squares
        p2.move_to(p.place)
        assert p.player.is_perceiving(p2)
        assert p2.player.is_perceiving(p)
        assert p.place in p2.player.observed_before_squares
        fm = self.find_player_unit(self.cp, "new_flyingmachine")
        assert not p.is_inside
        fm.load(p)
        assert p.is_inside
        assert not p2.player.is_perceiving(p)
        fm.unload_all()
        assert not p.is_inside
        assert p2.player.is_perceiving(p)
        p2.move_to(p2place)
        assert not p.player.is_perceiving(p2)
        assert not p2.player.is_perceiving(p)
        p2.move_to(p.place)
        assert p.player.is_perceiving(p2)
        assert p2.player.is_perceiving(p)
        p2.die()
        assert not self.cp2.is_perceiving(p)
        fm.load_all()
        fm.unload_all()
        fm.load_all()
        fm.unload_all()

    def testPerceptionAfterUnitDeath(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        assert self.cp.is_perceiving(p)
        assert p in self.cp.perception
        assert p not in [_.initial_model for _ in self.cp.memory]
        p2 = self.find_player_unit(self.cp2, "peasant")
        assert p2 not in [_.initial_model for _ in self.cp.memory]
        assert p2 not in self.cp.perception
        p.move_to(p2.place)
        assert self.cp.is_perceiving(p)
        assert p in self.cp.perception
        th2 = self.find_player_unit(self.cp2, "townhall")
        assert th2 in self.cp.perception
        p.die()
        assert th2 not in self.cp.perception
        assert th2 in [_.initial_model for _ in self.cp.memory]
        assert not self.cp.is_perceiving(p)
        assert p not in self.cp.perception
        assert p not in [_.initial_model for _ in self.cp.memory]

    def testPerceptionAfterUnitOwnershipChange(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        assert self.cp.is_perceiving(p)
        assert p in self.cp.perception
        assert p not in [_.initial_model for _ in self.cp.memory]
        p2 = self.find_player_unit(self.cp2, "peasant")
        assert p2 not in [_.initial_model for _ in self.cp.memory]
        assert p2 not in self.cp.perception
        p.move_to(p2.place)
        assert self.cp.is_perceiving(p)
        assert p in self.cp.perception
        th2 = self.find_player_unit(self.cp2, "townhall")
        assert th2 in self.cp.perception
        p.set_player(None)
        assert th2 not in self.cp.perception
        assert th2 in [_.initial_model for _ in self.cp.memory]
        assert not self.cp.is_perceiving(p)
        assert p not in self.cp.perception
        assert p in [_.initial_model for _ in self.cp.memory]

    def testMemoryOfResourceWhenAlliance(self):
        # Note: no unit with diagonal sight (air or tower)
        self.set_up((1, 1), map_name="jl1")
        p = self.find_player_unit(self.cp, "peasant")
        assert p.player.is_perceiving(p)
        assert self.cp2.is_perceiving(p)
        initial = p.place
        for o in self.w.grid["a2"].objects:
            assert not p.player.is_perceiving(o)
            assert not self.cp2.is_perceiving(o)
            assert o not in [_.initial_model for _ in p.player.memory]
            assert o not in p.player.perception
            assert o not in self.cp2.perception
        p.move_to(self.w.grid["a2"])
        for o in self.w.grid["a2"].objects:
            assert p.player.is_perceiving(o)
            assert self.cp2.is_perceiving(o)
            assert o not in [_.initial_model for _ in p.player.memory]
            assert o in p.player.perception
            assert o in self.cp2.perception
        p.move_to(initial)
        for o in self.w.grid["a2"].objects:
            assert not p.player.is_perceiving(o)
            assert not self.cp2.is_perceiving(o)
            assert o not in p.player.perception
            assert o not in self.cp2.perception
            assert o in [_.initial_model for _ in p.player.memory]

    def testHas(self):
        self.set_up()
        c = self.find_player_unit(self.cp, "castle")
        assert self.cp.has("castle")
        assert self.cp.has("keep")
        assert self.cp.has("townhall")
        th = self.find_player_unit(self.cp, "townhall")
        th.delete()
        assert self.cp.has("castle")
        assert self.cp.has("keep")
        assert self.cp.has("townhall")
        c.delete()
        assert not self.cp.has("castle")
        assert not self.cp.has("keep")
        assert not self.cp.has("townhall")

    def testHas2(self):
        self.set_up()
        c = self.find_player_unit(self.cp, "castle")
        assert self.cp.has("castle")
        assert self.cp.has("keep")
        assert self.cp.has("townhall")
        c.delete()
        assert not self.cp.has("castle")
        assert not self.cp.has("keep")
        assert self.cp.has("townhall")

    def testReact(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        p2 = self.find_player_unit(self.cp2, "peasant")
        self.assertTrue(p2.is_an_enemy(p))
        p.move_to(p2.place)
        self.assertTrue(p2.can_attack(p)) # (a bit too late to test this)
        self.assertEqual(p2.action_target, p) # "peasant should attack peasant"

    def testUpgradeTo(self):
        self.set_up()
        th = self.find_player_unit(self.cp, "townhall")
        self.cp.lang_add_units([th.place.name, "barracks"])
        self.assertEqual(self.cp.nb("keep"), 0)
        self.assertEqual(self.cp.nb("barracks"), 1)
        self.cp.resources = [100000, 100000]
        th.take_order(["upgrade_to", "keep"])
        assert th.orders
        self.assertFalse(th.orders[0].is_impossible)
        for _ in range(10000):
            th.update()
            if not th.orders:
                break
        assert not th.orders
        self.assertEqual(self.cp.nb("keep"), 1)
        self.assertEqual(th.place, None)
        self.assertTrue(th not in self.cp.units, "townhall still belongs to the player")

    def testAllied(self):
        # when allied
        self.set_up((1, 1), cloak=True)
        p = self.find_player_unit(self.cp, "peasant")
        p2 = self.find_player_unit(self.cp2, "peasant")
        th = self.find_player_unit(self.cp, "townhall")
        # allied: hostility
        self.assertFalse(p.is_an_enemy(p2))
        self.assertFalse(self.cp.is_an_enemy(self.cp2))
        # allied_vision
        self.assertTrue(self.cp.is_perceiving(p2))
        # allied: heal
        th.heal_level = 1 # force healing by the townhall (only the priest heals now)
        p2.hp = 0
        p2.move_to(p.place)
        for _ in range(1):
            th.update()
            th.slow_update()
            if p2.hp > 0:
                break
        assert p2.hp > 0
        # allied: cloak
        self.assertTrue(p.is_invisible_or_cloaked())
        self.assertTrue(p2.is_invisible_or_cloaked())
        # allied_victory
        self.assertTrue(self.cp.lang_no_enemy_left(None))

    def testAllied2(self):
        # when not allied
        self.set_up(cloak=True)
        p = self.find_player_unit(self.cp, "peasant")
        p2 = self.find_player_unit(self.cp2, "peasant")
        th = self.find_player_unit(self.cp, "townhall")
        # allied: hostility
        self.assertTrue(p.is_an_enemy(p2))
        self.assertTrue(self.cp.is_an_enemy(self.cp2))
        # allied_vision
        self.assertFalse(self.cp.is_perceiving(p2))
        # allied: heal
        p2.hp = 0
        p2.move_to(p.place)
        for _ in range(1):
            th.update()
            th.slow_update()
            if p2.hp > 0:
                break
        assert p2.hp == 0
        # allied: cloak
        self.assertTrue(p.is_invisible_or_cloaked())
        self.assertFalse(p2.is_invisible_or_cloaked())
        # allied_victory
        self.assertFalse(self.cp.lang_no_enemy_left(None))

    def testAlliedObserverAfterDefeat(self):
        # test bug #63: a defeated player shouldn't share the observer view with the team
        self.set_up((1, 1), map_name="jl1")
        self.cp2.observer_if_defeated = True
        # We won't check the observed squares because (at the moment)
        # it seems that the observed squares are not shared by allies,
        # only the objects in the squares.
        # Instead, we check the first object of the square.
        first_object_of_A2 = self.w.grid["a2"].objects[0]
        self.assertFalse(self.cp.is_perceiving(first_object_of_A2))
        self.assertFalse(self.cp2.is_perceiving(first_object_of_A2))
        # to avoid an error, disable temporarily store_score
        # (maybe remove this when store_score() won't rely on style anymore) 
        def do_nothing(): pass
        _backup = self.cp2.store_score
        self.cp2.store_score = do_nothing
        self.cp2.defeat()
        self.cp2.store_score = _backup
        self.assertFalse(self.cp.is_perceiving(first_object_of_A2)) # bug #63
        self.assertTrue(self.cp2.is_perceiving(first_object_of_A2)) # observer mode after defeat

    def testAI(self):
        self.set_up()
        th = self.find_player_unit(self.cp, "townhall")
        self.assertEqual(self.cp.nearest_warehouse(th.place, 0), th)
        self.assertEqual(self.cp.nearest_warehouse(th.place, 1), th)
        self.assertEqual(th.place.shortest_path_distance_to(th.place), 0)

    def testImperativeGo(self):        
        self.set_up()
        th = self.find_player_unit(self.cp, "townhall")
        p = self.find_player_unit(self.cp, "peasant")
        p.take_order(["go", th.id], imperative=True)
        self.assertEqual(th.hp, th.hp_max)
        for _ in range(100):
            p.update()
            if th.hp != th.hp_max:
                break
        self.assertNotEqual(th.hp, th.hp_max)

    def testImperativeGo2(self):        
        self.set_up()
        th = self.find_player_unit(self.cp, "townhall")
        f = self.find_player_unit(self.cp, "flyingmachine")
        f.take_order(["go", th.id], imperative=True)
        self.assertEqual(th.hp, th.hp_max)
        for _ in range(100):
            f.update()
            if th.hp != th.hp_max:
                break
        self.assertNotEqual(th.hp, th.hp_max)

    def testImperativeGo3(self):        
        self.set_up()
        th = self.find_player_unit(self.cp, "townhall")
        f = self.find_player_unit(self.cp, "dragon")
        f.take_order(["go", th.id], imperative=True)
        self.assertEqual(th.hp, th.hp_max)
        for _ in range(100):
            f.update()
            if th.hp != th.hp_max:
                break
        self.assertNotEqual(th.hp, th.hp_max)

    def testMoveSlowly(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        p.speed /= 100
        p.move_to(self.w.grid["a2"])
        p.take_order(["go", self.w.grid["a1"].id])
        x, y = p.x, p.y
        self.w.update() # for the order
        assert (x, y) == (p.x, p.y) # XXX not important
        self.w.update() # move
        assert (x, y) != (p.x, p.y)
        x2, y2 = p.x, p.y
        assert (x2, y2) == (p.x, p.y)

        # do this a second time => same result
        p.move_to(self.w.grid["a2"], x, y)
        assert (x, y) == (p.x, p.y)
        p.action_target = None
        p.take_order(["go", self.w.grid["a1"].id])
        assert (x, y) == (p.x, p.y)
        self.w.update() # for the order
        assert (x, y) == (p.x, p.y) # XXX not important
        self.w.update() # move
        assert (x, y) != (p.x, p.y)
        assert (x2, y2) == (p.x, p.y)

        # without collision => same result
        self.w.collision[p.airground_type].remove(p.x, p.y)
        p.collision = 0
        p.move_to(self.w.grid["a2"], x, y)
        assert (x, y) == (p.x, p.y)
        p.action_target = None
        p.take_order(["go", self.w.grid["a1"].id])
        assert (x, y) == (p.x, p.y)
        self.w.update() # for the order
        assert (x, y) == (p.x, p.y) # XXX not important
        self.w.update() # move
        assert (x, y) != (p.x, p.y)
        assert (x2, y2) == (p.x, p.y)

    def testDieToAirTransport(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        f = self.find_player_unit(self.cp, "new_flyingmachine")
        pl = f.place
        f.load(p)
        f.die()
        assert isinstance(pl.objects[-1], Corpse)
        assert pl.objects[-1].unit.type_name == "peasant"
        assert not p.place is pl

    def testSurviveToGroundTransport(self):
        self.set_up()
        p = self.find_player_unit(self.cp, "peasant")
        f = self.find_player_unit(self.cp, "new_flyingmachine")
        pl = f.place
        f.airground_type = "ground"
        f.load(p)
        f.die()
        assert not isinstance(pl.objects[-1], Corpse)
        assert p.place is pl


if __name__ == "__main__":
    unittest.main()

import random

from itertools import cycle
from unittest import TestCase, skip

from libros.game import (
    deal, Game, Player,
    ACTIONS, ACTION_PILE_CARD, ACTION_SHOW_CARD,
    ACTION_TAKE_CARD, ACTION_DISCARD_CARD,
)


class TestGame(TestCase):
    def test_deal(self):
        self.assertEqual(len(deal(4)), 80)
        self.assertEqual(len(deal(3)), 72)
        self.assertEqual(len(deal(2)), 60)

    def test_deal_cards(self):
        deck = deal(2, cards_to_remove=0, gold_to_remove=0)

        self.assertEqual(len(deck), 87)

        def _get_card(color, letter, value):
            for card in deck:
                if card == {"type": color, "letter": letter, "value": value}:
                    return card

        color_distribution = {
            'red': zip('ABCDEFGHI', '1' * 7 + '2' * 2),
            'orange': zip('ABCDEFGHI', '1' * 7 + '2' * 2),
            'green': zip('ABCDEFGHI', '1' * 7 + '2' * 2),
            'blue': zip('ABCDEFGHI', '2' * 4 + '3' * 3 + '4' * 2),
            'brown': zip('ABCDEFGHI', '2' * 4 + '3' * 3 + '4' * 2),
            'gold': zip(cycle([None]), '1' * 11 + '2' * 11 + '3' * 11),
            'change': zip(cycle([None]), [-2, -2, -1, -1, 0, 1, 1, 2, 2]),
        }

        count = 0

        for color, distribution in color_distribution.iteritems():
            for letter, value in distribution:
                self.assertIsNotNone(_get_card(color, letter, int(value)))
                count += 1

        self.assertEqual(count, 87)

    def test_join(self):
        player1 = Player()
        player2 = Player()
        game = Game()
        game.join(player1)
        self.assertEqual(game.state, 'waiting')
        self.assertEqual(game.player_count, 1)
        game.join(player2)
        self.assertEqual(game.state, 'waiting')
        self.assertEqual(game.player_count, 2)
        game.start()
        self.assertEqual(game.state, 'turn')

    def _start_game(self, num_players=2):
        players = [Player() for i in range(num_players)]

        game = Game()

        for player in players:
            game.join(player)

        game.start()

        self.assertEqual(game.state, 'turn')
        self.assertEqual(game.player_count, num_players)

        return game, players

    def _player_turn(self, game, action=None):
        active_player = game.active_player

        player, card, valid_actions = game.turn()

        if action is None or action not in valid_actions:
            action = random.choice(valid_actions)

        action = player.act(card, action)

        self.assertIn(action, ACTIONS)
        self.assertEqual(player, active_player)

        return player, card, action

    def _assert_cards_count(self, game, check_player,
                            pile, public, discarded, player):
        self.assertEqual(len(game.pile), pile)
        self.assertEqual(len(game.public), public)
        self.assertEqual(len(game.discarded), discarded)
        self.assertEqual(len(check_player.cards), player)

    def test_pile_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_PILE_CARD)

        self.assertEqual(action, ACTION_PILE_CARD)
        self._assert_cards_count(
            game, active_player, pile=1, public=0, discarded=0, player=0)

    def test_show_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_SHOW_CARD)

        self.assertEqual(action, ACTION_SHOW_CARD)
        self._assert_cards_count(
            game, active_player, pile=0, public=1, discarded=0, player=0)

    def test_take_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_TAKE_CARD)

        self.assertEqual(action, ACTION_TAKE_CARD)
        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=1)

    @skip("Skip until discard card is properly implemented")
    def test_discard_card(self):
        game, players = self._start_game()

        active_player = game.active_player

        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=0, player=0)

        player, card, action = self._player_turn(game, ACTION_DISCARD_CARD)

        self.assertEqual(action, ACTION_DISCARD_CARD)
        self._assert_cards_count(
            game, active_player, pile=0, public=0, discarded=1, player=0)

    def test_game(self):
        game, players = self._start_game()

        active_player = game.active_player
        deck_count = game.deck_count
        self.assertIn(active_player, players)

        self.assertTrue(all(die == 3 for die in game.dice.values()))

        for i in range(game.turns_per_player):
            player, card, action = self._player_turn(game)
            self.assertEqual(player, active_player)

        self.assertEqual(game.deck_count, deck_count - game.turns_per_player)

        self.assertEqual(game.public_count, game.player_count - 1)
        self.assertEqual(game.state, 'public')

        player, card, action = self._player_turn(game)

        next_active_player = game.active_player
        self.assertNotEqual(active_player, next_active_player)
        self.assertEqual(game.turns_left, 3)

    def test_using_dice_change_cards(self):
        game, players = self._start_game()
        card = {'kind': 'change', 'value': -1, 'letter': None}
        
        game.use_change_card(card, [])
        self.assertEqual(sum(game.dice.values()), 15)

        card['value'] = 2
        game.use_change_card(card, ['brown', 'red'])
        self.assertEqual(sum(game.dice.values()), 17)

        card['value'] = 0
        game.use_change_card(card, ['-blue'])
        self.assertEqual(sum(game.dice.values()), 16)

    def test_until_auction_phase_2_players(self):
        game, players = self._start_game(2)

        while game.state != 'auction':
            player, card, action = self._player_turn(game)

        player_cards = sum([len(p.cards) for p in players])
        total_cards = (game.discarded_count + game.public_count +
                       game.pile_count + player_cards)

        self.assertEqual(total_cards, 60)

    def test_until_auction_phase_3_players(self):
        game, players = self._start_game(3)

        while game.state != 'auction':
            player, card, action = self._player_turn(game)

        player_cards = sum([len(p.cards) for p in players])
        total_cards = (game.discarded_count + game.public_count +
                       game.pile_count + player_cards)

        self.assertEqual(total_cards, 72)

    def test_until_auction_phase_4_players(self):
        game, players = self._start_game(4)

        while game.state != 'auction':
            player, card, action = self._player_turn(game)

        player_cards = sum([len(p.cards) for p in players])
        total_cards = (game.discarded_count + game.public_count +
                       game.pile_count + player_cards)

        self.assertEqual(total_cards, 80)

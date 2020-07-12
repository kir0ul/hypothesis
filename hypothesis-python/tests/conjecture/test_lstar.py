# This file is part of Hypothesis, which may be found at
# https://github.com/HypothesisWorks/hypothesis/
#
# Most of this work is copyright (C) 2013-2020 David R. MacIver
# (david@drmaciver.com), but it contains contributions by others. See
# CONTRIBUTING.rst for a full list of people who may hold copyright, and
# consult the git log if you need to determine who owns an individual
# contribution.
#
# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at https://mozilla.org/MPL/2.0/.
#
# END HEADER

import itertools

from hypothesis.internal.conjecture.dfa.lstar import LStar


def test_can_learn_simple_predicate():
    learner = LStar(lambda s: len(s) >= 3)

    learner.learn(bytes(3))

    dfa = learner.dfa
    assert dfa.start == 0
    assert dfa.transition(0, 0) == 1
    assert dfa.transition(1, 0) == 2
    assert dfa.transition(2, 0) == 3
    assert dfa.transition(3, 0) == 3

    assert not dfa.is_accepting(0)
    assert not dfa.is_accepting(1)
    assert not dfa.is_accepting(2)
    assert dfa.is_accepting(3)


def test_relearning_does_not_change_generation():
    learner = LStar(lambda s: len(s) >= 3)

    prev = learner.generation
    learner.learn(bytes(3))
    assert prev != learner.generation

    prev = learner.generation
    learner.learn(bytes(3))
    assert prev == learner.generation


def test_can_learn_dead_nodes():
    learner = LStar(lambda s: len(s) == 4 and max(s) <= 1)

    learner.learn(bytes(4))

    assert learner.dfa.matches(bytes(4))
    assert learner.dfa.matches(bytes([1] * 4))

    # Need a length 5 string to distinguish this from
    # something that just loops back to zero.
    learner.learn([2, 0, 0, 0, 0])

    dfa = learner.dfa

    assert dfa.is_dead(dfa.transition(dfa.start, 2))
    assert dfa.is_dead(dfa.transition(dfa.start, 3))


def test_iterates_over_learned_strings():
    upper_bound = bytes([1, 2])
    learner = LStar(lambda s: len(s) == 2 and max(s) <= 5 and s <= upper_bound)
    learner.learn(upper_bound)
    learner.learn([1, 2, 0])
    learner.learn([6, 1, 2])
    learner.learn([1, 3])
    learner.learn([0, 5])
    learner.learn([0, 6])

    dfa = learner.dfa
    n = 9
    matches = list(itertools.islice(dfa, n + 1))
    assert len(matches) == n


def test_iteration_with_dead_nodes():
    learner = LStar(lambda s: len(s) == 3 and max(s) <= 1 and s[1] == 0)
    learner.learn([1, 0, 1])
    learner.learn([1, 1, 1])
    learner.learn([0, 1, 1])
    learner.learn([1, 1, 0])
    learner.learn([1, 1, 1, 0, 1])

    dfa = learner.dfa
    i = dfa.transition(dfa.start, 1)
    assert not dfa.is_dead(i)
    assert dfa.is_dead(dfa.transition(i, 2))

    assert list(learner.dfa) == [
        bytes([0, 0, 0]),
        bytes([0, 0, 1]),
        bytes([1, 0, 0]),
        bytes([1, 0, 1]),
    ]

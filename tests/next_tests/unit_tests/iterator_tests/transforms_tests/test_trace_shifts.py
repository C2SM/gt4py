# GT4Py - GridTools Framework
#
# Copyright (c) 2014-2023, ETH Zurich
# All rights reserved.
#
# This file is part of the GT4Py project and the GridTools framework.
# GT4Py is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or any later
# version. See the LICENSE.txt file at the top-level directory of this
# distribution for a copy of the license or check <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gt4py.next.iterator import ir, ir_makers as im
from gt4py.next.iterator.transforms.trace_shifts import ALL_NEIGHBORS, TraceShifts


def test_trivial():
    testee = ir.StencilClosure(
        stencil=ir.SymRef(id="deref"),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {"inp": [()]}

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected


def test_shift():
    testee = ir.StencilClosure(
        stencil=ir.Lambda(
            expr=ir.FunCall(
                fun=ir.SymRef(id="deref"),
                args=[
                    ir.FunCall(
                        fun=ir.FunCall(
                            fun=ir.SymRef(id="shift"),
                            args=[ir.OffsetLiteral(value="I"), ir.OffsetLiteral(value=1)],
                        ),
                        args=[ir.SymRef(id="x")],
                    )
                ],
            ),
            params=[ir.Sym(id="x")],
        ),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {"inp": [(ir.OffsetLiteral(value="I"), ir.OffsetLiteral(value=1))]}

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected


def test_lift():
    testee = ir.StencilClosure(
        stencil=ir.Lambda(
            expr=ir.FunCall(
                fun=ir.SymRef(id="deref"),
                args=[
                    ir.FunCall(
                        fun=ir.FunCall(fun=ir.SymRef(id="lift"), args=[ir.SymRef(id="deref")]),
                        args=[
                            ir.FunCall(
                                fun=ir.FunCall(
                                    fun=ir.SymRef(id="shift"),
                                    args=[ir.OffsetLiteral(value="I"), ir.OffsetLiteral(value=1)],
                                ),
                                args=[ir.SymRef(id="x")],
                            )
                        ],
                    )
                ],
            ),
            params=[ir.Sym(id="x")],
        ),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {"inp": [(ir.OffsetLiteral(value="I"), ir.OffsetLiteral(value=1))]}

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected


def test_neighbors():
    testee = ir.StencilClosure(
        stencil=ir.Lambda(
            expr=ir.FunCall(
                fun=ir.SymRef(id="neighbors"),
                args=[ir.OffsetLiteral(value="O"), ir.SymRef(id="x")],
            ),
            params=[ir.Sym(id="x")],
        ),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {
        "inp": [
            (
                ir.OffsetLiteral(value="O"),
                ALL_NEIGHBORS,
            )
        ]
    }

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected


def test_reduce():
    testee = ir.StencilClosure(
        # λ(inp) → reduce(plus, init)(·inp)
        stencil=ir.Lambda(
            params=[ir.Sym(id="inp")],
            expr=ir.FunCall(
                fun=ir.FunCall(
                    fun=ir.SymRef(id="reduce"), args=[ir.SymRef(id="plus"), ir.SymRef(id="init")]
                ),
                args=[ir.FunCall(fun=ir.SymRef(id="deref"), args=[ir.SymRef(id="inp")])],
            ),
        ),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {"inp": [()]}

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected


def test_shifted_literal():
    "Test shifting an applied lift of a stencil returning a constant / literal works."
    testee = ir.StencilClosure(
        # λ(x) → ·⟪Iₒ, 1ₒ⟫((↑(λ() → 1))())
        stencil=im.lambda_("x")(im.deref(im.shift("I", 1)(im.lift(im.lambda_()(1))()))),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {"inp": []}

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected


def test_tuple_get_on_closure_input():
    testee = ir.StencilClosure(
        # λ(x) → (·⟪Iₒ, 1ₒ⟫(x))[0]
        stencil=im.lambda_("x")(im.tuple_get(0, im.deref(im.shift("I", 1)("x")))),
        inputs=[ir.SymRef(id="inp")],
        output=ir.SymRef(id="out"),
        domain=ir.FunCall(fun=ir.SymRef(id="cartesian_domain"), args=[]),
    )
    expected = {"inp": [(ir.OffsetLiteral(value="I"), ir.OffsetLiteral(value=1))]}

    actual = dict()
    TraceShifts().visit(testee, shifts=actual)
    assert actual == expected

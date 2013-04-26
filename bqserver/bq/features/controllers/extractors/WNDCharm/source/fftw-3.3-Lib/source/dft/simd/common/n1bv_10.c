/*
 * Copyright (c) 2003, 2007-11 Matteo Frigo
 * Copyright (c) 2003, 2007-11 Massachusetts Institute of Technology
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
 *
 */

/* This file was automatically generated --- DO NOT EDIT */
/* Generated on Sat Apr 28 11:00:09 EDT 2012 */

#include "codelet-dft.h"

#ifdef HAVE_FMA

/* Generated by: ../../../genfft/gen_notw_c.native -fma -reorder-insns -schedule-for-pipeline -simd -compact -variables 4 -pipeline-latency 8 -sign 1 -n 10 -name n1bv_10 -include n1b.h */

/*
 * This function contains 42 FP additions, 22 FP multiplications,
 * (or, 24 additions, 4 multiplications, 18 fused multiply/add),
 * 43 stack variables, 4 constants, and 20 memory accesses
 */
#include "n1b.h"

static void n1bv_10(const R *ri, const R *ii, R *ro, R *io, stride is, stride os, INT v, INT ivs, INT ovs)
{
     DVK(KP559016994, +0.559016994374947424102293417182819058860154590);
     DVK(KP250000000, +0.250000000000000000000000000000000000000000000);
     DVK(KP618033988, +0.618033988749894848204586834365638117720309180);
     DVK(KP951056516, +0.951056516295153572116439333379382143405698634);
     {
	  INT i;
	  const R *xi;
	  R *xo;
	  xi = ii;
	  xo = io;
	  for (i = v; i > 0; i = i - VL, xi = xi + (VL * ivs), xo = xo + (VL * ovs), MAKE_VOLATILE_STRIDE(is), MAKE_VOLATILE_STRIDE(os)) {
	       V Tb, Tr, T3, Ts, T6, Tw, Tg, Tt, T9, Tc, T1, T2;
	       T1 = LD(&(xi[0]), ivs, &(xi[0]));
	       T2 = LD(&(xi[WS(is, 5)]), ivs, &(xi[WS(is, 1)]));
	       {
		    V T4, T5, Te, Tf, T7, T8;
		    T4 = LD(&(xi[WS(is, 2)]), ivs, &(xi[0]));
		    T5 = LD(&(xi[WS(is, 7)]), ivs, &(xi[WS(is, 1)]));
		    Te = LD(&(xi[WS(is, 6)]), ivs, &(xi[0]));
		    Tf = LD(&(xi[WS(is, 1)]), ivs, &(xi[WS(is, 1)]));
		    T7 = LD(&(xi[WS(is, 8)]), ivs, &(xi[0]));
		    T8 = LD(&(xi[WS(is, 3)]), ivs, &(xi[WS(is, 1)]));
		    Tb = LD(&(xi[WS(is, 4)]), ivs, &(xi[0]));
		    Tr = VADD(T1, T2);
		    T3 = VSUB(T1, T2);
		    Ts = VADD(T4, T5);
		    T6 = VSUB(T4, T5);
		    Tw = VADD(Te, Tf);
		    Tg = VSUB(Te, Tf);
		    Tt = VADD(T7, T8);
		    T9 = VSUB(T7, T8);
		    Tc = LD(&(xi[WS(is, 9)]), ivs, &(xi[WS(is, 1)]));
	       }
	       {
		    V TD, Tu, Tm, Ta, Td, Tv;
		    TD = VSUB(Ts, Tt);
		    Tu = VADD(Ts, Tt);
		    Tm = VSUB(T6, T9);
		    Ta = VADD(T6, T9);
		    Td = VSUB(Tb, Tc);
		    Tv = VADD(Tb, Tc);
		    {
			 V TC, Tx, Tn, Th;
			 TC = VSUB(Tv, Tw);
			 Tx = VADD(Tv, Tw);
			 Tn = VSUB(Td, Tg);
			 Th = VADD(Td, Tg);
			 {
			      V Ty, TA, TE, TG, Ti, Tk, To, Tq, Tz, Tj;
			      Ty = VADD(Tu, Tx);
			      TA = VSUB(Tu, Tx);
			      TE = VMUL(LDK(KP951056516), VFNMS(LDK(KP618033988), TD, TC));
			      TG = VMUL(LDK(KP951056516), VFMA(LDK(KP618033988), TC, TD));
			      Ti = VADD(Ta, Th);
			      Tk = VSUB(Ta, Th);
			      To = VMUL(LDK(KP951056516), VFMA(LDK(KP618033988), Tn, Tm));
			      Tq = VMUL(LDK(KP951056516), VFNMS(LDK(KP618033988), Tm, Tn));
			      Tz = VFNMS(LDK(KP250000000), Ty, Tr);
			      ST(&(xo[0]), VADD(Tr, Ty), ovs, &(xo[0]));
			      Tj = VFNMS(LDK(KP250000000), Ti, T3);
			      ST(&(xo[WS(os, 5)]), VADD(T3, Ti), ovs, &(xo[WS(os, 1)]));
			      {
				   V TB, TF, Tl, Tp;
				   TB = VFNMS(LDK(KP559016994), TA, Tz);
				   TF = VFMA(LDK(KP559016994), TA, Tz);
				   Tl = VFMA(LDK(KP559016994), Tk, Tj);
				   Tp = VFNMS(LDK(KP559016994), Tk, Tj);
				   ST(&(xo[WS(os, 4)]), VFNMSI(TG, TF), ovs, &(xo[0]));
				   ST(&(xo[WS(os, 6)]), VFMAI(TG, TF), ovs, &(xo[0]));
				   ST(&(xo[WS(os, 8)]), VFMAI(TE, TB), ovs, &(xo[0]));
				   ST(&(xo[WS(os, 2)]), VFNMSI(TE, TB), ovs, &(xo[0]));
				   ST(&(xo[WS(os, 3)]), VFMAI(Tq, Tp), ovs, &(xo[WS(os, 1)]));
				   ST(&(xo[WS(os, 7)]), VFNMSI(Tq, Tp), ovs, &(xo[WS(os, 1)]));
				   ST(&(xo[WS(os, 9)]), VFNMSI(To, Tl), ovs, &(xo[WS(os, 1)]));
				   ST(&(xo[WS(os, 1)]), VFMAI(To, Tl), ovs, &(xo[WS(os, 1)]));
			      }
			 }
		    }
	       }
	  }
     }
     VLEAVE();
}

static const kdft_desc desc = { 10, XSIMD_STRING("n1bv_10"), {24, 4, 18, 0}, &GENUS, 0, 0, 0, 0 };

void XSIMD(codelet_n1bv_10) (planner *p) {
     X(kdft_register) (p, n1bv_10, &desc);
}

#else				/* HAVE_FMA */

/* Generated by: ../../../genfft/gen_notw_c.native -simd -compact -variables 4 -pipeline-latency 8 -sign 1 -n 10 -name n1bv_10 -include n1b.h */

/*
 * This function contains 42 FP additions, 12 FP multiplications,
 * (or, 36 additions, 6 multiplications, 6 fused multiply/add),
 * 33 stack variables, 4 constants, and 20 memory accesses
 */
#include "n1b.h"

static void n1bv_10(const R *ri, const R *ii, R *ro, R *io, stride is, stride os, INT v, INT ivs, INT ovs)
{
     DVK(KP250000000, +0.250000000000000000000000000000000000000000000);
     DVK(KP559016994, +0.559016994374947424102293417182819058860154590);
     DVK(KP587785252, +0.587785252292473129168705954639072768597652438);
     DVK(KP951056516, +0.951056516295153572116439333379382143405698634);
     {
	  INT i;
	  const R *xi;
	  R *xo;
	  xi = ii;
	  xo = io;
	  for (i = v; i > 0; i = i - VL, xi = xi + (VL * ivs), xo = xo + (VL * ovs), MAKE_VOLATILE_STRIDE(is), MAKE_VOLATILE_STRIDE(os)) {
	       V Tl, Ty, T7, Te, Tw, Tt, Tz, TA, TB, Tg, Th, Tm, Tj, Tk;
	       Tj = LD(&(xi[0]), ivs, &(xi[0]));
	       Tk = LD(&(xi[WS(is, 5)]), ivs, &(xi[WS(is, 1)]));
	       Tl = VSUB(Tj, Tk);
	       Ty = VADD(Tj, Tk);
	       {
		    V T3, Tr, Td, Tv, T6, Ts, Ta, Tu;
		    {
			 V T1, T2, Tb, Tc;
			 T1 = LD(&(xi[WS(is, 2)]), ivs, &(xi[0]));
			 T2 = LD(&(xi[WS(is, 7)]), ivs, &(xi[WS(is, 1)]));
			 T3 = VSUB(T1, T2);
			 Tr = VADD(T1, T2);
			 Tb = LD(&(xi[WS(is, 6)]), ivs, &(xi[0]));
			 Tc = LD(&(xi[WS(is, 1)]), ivs, &(xi[WS(is, 1)]));
			 Td = VSUB(Tb, Tc);
			 Tv = VADD(Tb, Tc);
		    }
		    {
			 V T4, T5, T8, T9;
			 T4 = LD(&(xi[WS(is, 8)]), ivs, &(xi[0]));
			 T5 = LD(&(xi[WS(is, 3)]), ivs, &(xi[WS(is, 1)]));
			 T6 = VSUB(T4, T5);
			 Ts = VADD(T4, T5);
			 T8 = LD(&(xi[WS(is, 4)]), ivs, &(xi[0]));
			 T9 = LD(&(xi[WS(is, 9)]), ivs, &(xi[WS(is, 1)]));
			 Ta = VSUB(T8, T9);
			 Tu = VADD(T8, T9);
		    }
		    T7 = VSUB(T3, T6);
		    Te = VSUB(Ta, Td);
		    Tw = VSUB(Tu, Tv);
		    Tt = VSUB(Tr, Ts);
		    Tz = VADD(Tr, Ts);
		    TA = VADD(Tu, Tv);
		    TB = VADD(Tz, TA);
		    Tg = VADD(T3, T6);
		    Th = VADD(Ta, Td);
		    Tm = VADD(Tg, Th);
	       }
	       ST(&(xo[WS(os, 5)]), VADD(Tl, Tm), ovs, &(xo[WS(os, 1)]));
	       ST(&(xo[0]), VADD(Ty, TB), ovs, &(xo[0]));
	       {
		    V Tf, Tq, To, Tp, Ti, Tn;
		    Tf = VBYI(VFMA(LDK(KP951056516), T7, VMUL(LDK(KP587785252), Te)));
		    Tq = VBYI(VFNMS(LDK(KP951056516), Te, VMUL(LDK(KP587785252), T7)));
		    Ti = VMUL(LDK(KP559016994), VSUB(Tg, Th));
		    Tn = VFNMS(LDK(KP250000000), Tm, Tl);
		    To = VADD(Ti, Tn);
		    Tp = VSUB(Tn, Ti);
		    ST(&(xo[WS(os, 1)]), VADD(Tf, To), ovs, &(xo[WS(os, 1)]));
		    ST(&(xo[WS(os, 7)]), VADD(Tq, Tp), ovs, &(xo[WS(os, 1)]));
		    ST(&(xo[WS(os, 9)]), VSUB(To, Tf), ovs, &(xo[WS(os, 1)]));
		    ST(&(xo[WS(os, 3)]), VSUB(Tp, Tq), ovs, &(xo[WS(os, 1)]));
	       }
	       {
		    V Tx, TG, TE, TF, TC, TD;
		    Tx = VBYI(VFNMS(LDK(KP951056516), Tw, VMUL(LDK(KP587785252), Tt)));
		    TG = VBYI(VFMA(LDK(KP951056516), Tt, VMUL(LDK(KP587785252), Tw)));
		    TC = VFNMS(LDK(KP250000000), TB, Ty);
		    TD = VMUL(LDK(KP559016994), VSUB(Tz, TA));
		    TE = VSUB(TC, TD);
		    TF = VADD(TD, TC);
		    ST(&(xo[WS(os, 2)]), VADD(Tx, TE), ovs, &(xo[0]));
		    ST(&(xo[WS(os, 6)]), VADD(TG, TF), ovs, &(xo[0]));
		    ST(&(xo[WS(os, 8)]), VSUB(TE, Tx), ovs, &(xo[0]));
		    ST(&(xo[WS(os, 4)]), VSUB(TF, TG), ovs, &(xo[0]));
	       }
	  }
     }
     VLEAVE();
}

static const kdft_desc desc = { 10, XSIMD_STRING("n1bv_10"), {36, 6, 6, 0}, &GENUS, 0, 0, 0, 0 };

void XSIMD(codelet_n1bv_10) (planner *p) {
     X(kdft_register) (p, n1bv_10, &desc);
}

#endif				/* HAVE_FMA */

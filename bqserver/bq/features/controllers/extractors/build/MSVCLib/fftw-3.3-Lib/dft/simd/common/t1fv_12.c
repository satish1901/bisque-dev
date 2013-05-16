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
/* Generated on Sat Apr 28 11:01:09 EDT 2012 */

#include "codelet-dft.h"

#ifdef HAVE_FMA

/* Generated by: ../../../genfft/gen_twiddle_c.native -fma -reorder-insns -schedule-for-pipeline -simd -compact -variables 4 -pipeline-latency 8 -n 12 -name t1fv_12 -include t1f.h */

/*
 * This function contains 59 FP additions, 42 FP multiplications,
 * (or, 41 additions, 24 multiplications, 18 fused multiply/add),
 * 41 stack variables, 2 constants, and 24 memory accesses
 */
#include "t1f.h"

static void t1fv_12(R *ri, R *ii, const R *W, stride rs, INT mb, INT me, INT ms)
{
     DVK(KP866025403, +0.866025403784438646763723170752936183471402627);
     DVK(KP500000000, +0.500000000000000000000000000000000000000000000);
     {
	  INT m;
	  R *x;
	  x = ri;
	  for (m = mb, W = W + (mb * ((TWVL / VL) * 22)); m < me; m = m + VL, x = x + (VL * ms), W = W + (TWVL * 22), MAKE_VOLATILE_STRIDE(rs)) {
	       V Tq, Ti, T7, TQ, Tu, TA, TU, Tk, TR, Tf, TE, TM;
	       {
		    V T9, TC, Tj, TD, Te;
		    {
			 V T1, T4, T2, Tm, Tx, To;
			 T1 = LD(&(x[0]), ms, &(x[0]));
			 T4 = LD(&(x[WS(rs, 8)]), ms, &(x[0]));
			 T2 = LD(&(x[WS(rs, 4)]), ms, &(x[0]));
			 Tm = LD(&(x[WS(rs, 1)]), ms, &(x[WS(rs, 1)]));
			 Tx = LD(&(x[WS(rs, 9)]), ms, &(x[WS(rs, 1)]));
			 To = LD(&(x[WS(rs, 5)]), ms, &(x[WS(rs, 1)]));
			 {
			      V T5, T3, Tn, Ty, Tp, Td, Tb, T8, Tc, Ta;
			      T8 = LD(&(x[WS(rs, 6)]), ms, &(x[0]));
			      Tc = LD(&(x[WS(rs, 2)]), ms, &(x[0]));
			      Ta = LD(&(x[WS(rs, 10)]), ms, &(x[0]));
			      T5 = BYTWJ(&(W[TWVL * 14]), T4);
			      T3 = BYTWJ(&(W[TWVL * 6]), T2);
			      Tn = BYTWJ(&(W[0]), Tm);
			      Ty = BYTWJ(&(W[TWVL * 16]), Tx);
			      Tp = BYTWJ(&(W[TWVL * 8]), To);
			      T9 = BYTWJ(&(W[TWVL * 10]), T8);
			      Td = BYTWJ(&(W[TWVL * 2]), Tc);
			      Tb = BYTWJ(&(W[TWVL * 18]), Ta);
			      {
				   V Th, T6, Tt, Tz;
				   Th = LD(&(x[WS(rs, 11)]), ms, &(x[WS(rs, 1)]));
				   TC = VSUB(T5, T3);
				   T6 = VADD(T3, T5);
				   Tt = LD(&(x[WS(rs, 3)]), ms, &(x[WS(rs, 1)]));
				   Tz = VADD(Tn, Tp);
				   Tq = VSUB(Tn, Tp);
				   Tj = LD(&(x[WS(rs, 7)]), ms, &(x[WS(rs, 1)]));
				   TD = VSUB(Td, Tb);
				   Te = VADD(Tb, Td);
				   Ti = BYTWJ(&(W[TWVL * 20]), Th);
				   T7 = VFNMS(LDK(KP500000000), T6, T1);
				   TQ = VADD(T1, T6);
				   Tu = BYTWJ(&(W[TWVL * 4]), Tt);
				   TA = VFNMS(LDK(KP500000000), Tz, Ty);
				   TU = VADD(Ty, Tz);
			      }
			 }
		    }
		    Tk = BYTWJ(&(W[TWVL * 12]), Tj);
		    TR = VADD(T9, Te);
		    Tf = VFNMS(LDK(KP500000000), Te, T9);
		    TE = VSUB(TC, TD);
		    TM = VADD(TC, TD);
	       }
	       {
		    V Tv, Tl, TI, Tg, TW, TS;
		    Tv = VADD(Tk, Ti);
		    Tl = VSUB(Ti, Tk);
		    TI = VADD(T7, Tf);
		    Tg = VSUB(T7, Tf);
		    TW = VADD(TQ, TR);
		    TS = VSUB(TQ, TR);
		    {
			 V TT, Tw, TL, Tr;
			 TT = VADD(Tu, Tv);
			 Tw = VFNMS(LDK(KP500000000), Tv, Tu);
			 TL = VSUB(Tl, Tq);
			 Tr = VADD(Tl, Tq);
			 {
			      V TP, TN, TG, Ts, TO, TK, TH, TF;
			      {
				   V TX, TV, TJ, TB;
				   TX = VADD(TT, TU);
				   TV = VSUB(TT, TU);
				   TJ = VADD(Tw, TA);
				   TB = VSUB(Tw, TA);
				   TP = VMUL(LDK(KP866025403), VADD(TM, TL));
				   TN = VMUL(LDK(KP866025403), VSUB(TL, TM));
				   TG = VFNMS(LDK(KP866025403), Tr, Tg);
				   Ts = VFMA(LDK(KP866025403), Tr, Tg);
				   ST(&(x[WS(rs, 6)]), VSUB(TW, TX), ms, &(x[0]));
				   ST(&(x[0]), VADD(TW, TX), ms, &(x[0]));
				   ST(&(x[WS(rs, 3)]), VFMAI(TV, TS), ms, &(x[WS(rs, 1)]));
				   ST(&(x[WS(rs, 9)]), VFNMSI(TV, TS), ms, &(x[WS(rs, 1)]));
				   TO = VADD(TI, TJ);
				   TK = VSUB(TI, TJ);
				   TH = VFMA(LDK(KP866025403), TE, TB);
				   TF = VFNMS(LDK(KP866025403), TE, TB);
			      }
			      ST(&(x[WS(rs, 4)]), VFMAI(TP, TO), ms, &(x[0]));
			      ST(&(x[WS(rs, 8)]), VFNMSI(TP, TO), ms, &(x[0]));
			      ST(&(x[WS(rs, 10)]), VFNMSI(TN, TK), ms, &(x[0]));
			      ST(&(x[WS(rs, 2)]), VFMAI(TN, TK), ms, &(x[0]));
			      ST(&(x[WS(rs, 5)]), VFNMSI(TH, TG), ms, &(x[WS(rs, 1)]));
			      ST(&(x[WS(rs, 7)]), VFMAI(TH, TG), ms, &(x[WS(rs, 1)]));
			      ST(&(x[WS(rs, 11)]), VFMAI(TF, Ts), ms, &(x[WS(rs, 1)]));
			      ST(&(x[WS(rs, 1)]), VFNMSI(TF, Ts), ms, &(x[WS(rs, 1)]));
			 }
		    }
	       }
	  }
     }
     VLEAVE();
}

static const tw_instr twinstr[] = {
     VTW(0, 1),
     VTW(0, 2),
     VTW(0, 3),
     VTW(0, 4),
     VTW(0, 5),
     VTW(0, 6),
     VTW(0, 7),
     VTW(0, 8),
     VTW(0, 9),
     VTW(0, 10),
     VTW(0, 11),
     {TW_NEXT, VL, 0}
};

static const ct_desc desc = { 12, XSIMD_STRING("t1fv_12"), twinstr, &GENUS, {41, 24, 18, 0}, 0, 0, 0 };

void XSIMD(codelet_t1fv_12) (planner *p) {
     X(kdft_dit_register) (p, t1fv_12, &desc);
}
#else				/* HAVE_FMA */

/* Generated by: ../../../genfft/gen_twiddle_c.native -simd -compact -variables 4 -pipeline-latency 8 -n 12 -name t1fv_12 -include t1f.h */

/*
 * This function contains 59 FP additions, 30 FP multiplications,
 * (or, 55 additions, 26 multiplications, 4 fused multiply/add),
 * 28 stack variables, 2 constants, and 24 memory accesses
 */
#include "t1f.h"

static void t1fv_12(R *ri, R *ii, const R *W, stride rs, INT mb, INT me, INT ms)
{
     DVK(KP866025403, +0.866025403784438646763723170752936183471402627);
     DVK(KP500000000, +0.500000000000000000000000000000000000000000000);
     {
	  INT m;
	  R *x;
	  x = ri;
	  for (m = mb, W = W + (mb * ((TWVL / VL) * 22)); m < me; m = m + VL, x = x + (VL * ms), W = W + (TWVL * 22), MAKE_VOLATILE_STRIDE(rs)) {
	       V T1, TH, T6, TA, Tq, TE, Tv, TL, T9, TI, Te, TB, Ti, TD, Tn;
	       V TK;
	       {
		    V T5, T3, T4, T2;
		    T1 = LD(&(x[0]), ms, &(x[0]));
		    T4 = LD(&(x[WS(rs, 8)]), ms, &(x[0]));
		    T5 = BYTWJ(&(W[TWVL * 14]), T4);
		    T2 = LD(&(x[WS(rs, 4)]), ms, &(x[0]));
		    T3 = BYTWJ(&(W[TWVL * 6]), T2);
		    TH = VSUB(T5, T3);
		    T6 = VADD(T3, T5);
		    TA = VFNMS(LDK(KP500000000), T6, T1);
	       }
	       {
		    V Tu, Ts, Tp, Tt, Tr;
		    Tp = LD(&(x[WS(rs, 9)]), ms, &(x[WS(rs, 1)]));
		    Tq = BYTWJ(&(W[TWVL * 16]), Tp);
		    Tt = LD(&(x[WS(rs, 5)]), ms, &(x[WS(rs, 1)]));
		    Tu = BYTWJ(&(W[TWVL * 8]), Tt);
		    Tr = LD(&(x[WS(rs, 1)]), ms, &(x[WS(rs, 1)]));
		    Ts = BYTWJ(&(W[0]), Tr);
		    TE = VSUB(Tu, Ts);
		    Tv = VADD(Ts, Tu);
		    TL = VFNMS(LDK(KP500000000), Tv, Tq);
	       }
	       {
		    V Td, Tb, T8, Tc, Ta;
		    T8 = LD(&(x[WS(rs, 6)]), ms, &(x[0]));
		    T9 = BYTWJ(&(W[TWVL * 10]), T8);
		    Tc = LD(&(x[WS(rs, 2)]), ms, &(x[0]));
		    Td = BYTWJ(&(W[TWVL * 2]), Tc);
		    Ta = LD(&(x[WS(rs, 10)]), ms, &(x[0]));
		    Tb = BYTWJ(&(W[TWVL * 18]), Ta);
		    TI = VSUB(Td, Tb);
		    Te = VADD(Tb, Td);
		    TB = VFNMS(LDK(KP500000000), Te, T9);
	       }
	       {
		    V Tm, Tk, Th, Tl, Tj;
		    Th = LD(&(x[WS(rs, 3)]), ms, &(x[WS(rs, 1)]));
		    Ti = BYTWJ(&(W[TWVL * 4]), Th);
		    Tl = LD(&(x[WS(rs, 11)]), ms, &(x[WS(rs, 1)]));
		    Tm = BYTWJ(&(W[TWVL * 20]), Tl);
		    Tj = LD(&(x[WS(rs, 7)]), ms, &(x[WS(rs, 1)]));
		    Tk = BYTWJ(&(W[TWVL * 12]), Tj);
		    TD = VSUB(Tm, Tk);
		    Tn = VADD(Tk, Tm);
		    TK = VFNMS(LDK(KP500000000), Tn, Ti);
	       }
	       {
		    V Tg, Ty, Tx, Tz;
		    {
			 V T7, Tf, To, Tw;
			 T7 = VADD(T1, T6);
			 Tf = VADD(T9, Te);
			 Tg = VSUB(T7, Tf);
			 Ty = VADD(T7, Tf);
			 To = VADD(Ti, Tn);
			 Tw = VADD(Tq, Tv);
			 Tx = VBYI(VSUB(To, Tw));
			 Tz = VADD(To, Tw);
		    }
		    ST(&(x[WS(rs, 9)]), VSUB(Tg, Tx), ms, &(x[WS(rs, 1)]));
		    ST(&(x[0]), VADD(Ty, Tz), ms, &(x[0]));
		    ST(&(x[WS(rs, 3)]), VADD(Tg, Tx), ms, &(x[WS(rs, 1)]));
		    ST(&(x[WS(rs, 6)]), VSUB(Ty, Tz), ms, &(x[0]));
	       }
	       {
		    V TS, TW, TV, TX;
		    {
			 V TQ, TR, TT, TU;
			 TQ = VADD(TA, TB);
			 TR = VADD(TK, TL);
			 TS = VSUB(TQ, TR);
			 TW = VADD(TQ, TR);
			 TT = VADD(TD, TE);
			 TU = VADD(TH, TI);
			 TV = VBYI(VMUL(LDK(KP866025403), VSUB(TT, TU)));
			 TX = VBYI(VMUL(LDK(KP866025403), VADD(TU, TT)));
		    }
		    ST(&(x[WS(rs, 10)]), VSUB(TS, TV), ms, &(x[0]));
		    ST(&(x[WS(rs, 4)]), VADD(TW, TX), ms, &(x[0]));
		    ST(&(x[WS(rs, 2)]), VADD(TS, TV), ms, &(x[0]));
		    ST(&(x[WS(rs, 8)]), VSUB(TW, TX), ms, &(x[0]));
	       }
	       {
		    V TG, TP, TN, TO;
		    {
			 V TC, TF, TJ, TM;
			 TC = VSUB(TA, TB);
			 TF = VMUL(LDK(KP866025403), VSUB(TD, TE));
			 TG = VSUB(TC, TF);
			 TP = VADD(TC, TF);
			 TJ = VMUL(LDK(KP866025403), VSUB(TH, TI));
			 TM = VSUB(TK, TL);
			 TN = VBYI(VADD(TJ, TM));
			 TO = VBYI(VSUB(TJ, TM));
		    }
		    ST(&(x[WS(rs, 5)]), VSUB(TG, TN), ms, &(x[WS(rs, 1)]));
		    ST(&(x[WS(rs, 11)]), VSUB(TP, TO), ms, &(x[WS(rs, 1)]));
		    ST(&(x[WS(rs, 7)]), VADD(TN, TG), ms, &(x[WS(rs, 1)]));
		    ST(&(x[WS(rs, 1)]), VADD(TO, TP), ms, &(x[WS(rs, 1)]));
	       }
	  }
     }
     VLEAVE();
}

static const tw_instr twinstr[] = {
     VTW(0, 1),
     VTW(0, 2),
     VTW(0, 3),
     VTW(0, 4),
     VTW(0, 5),
     VTW(0, 6),
     VTW(0, 7),
     VTW(0, 8),
     VTW(0, 9),
     VTW(0, 10),
     VTW(0, 11),
     {TW_NEXT, VL, 0}
};

static const ct_desc desc = { 12, XSIMD_STRING("t1fv_12"), twinstr, &GENUS, {55, 26, 4, 0}, 0, 0, 0 };

void XSIMD(codelet_t1fv_12) (planner *p) {
     X(kdft_dit_register) (p, t1fv_12, &desc);
}
#endif				/* HAVE_FMA */

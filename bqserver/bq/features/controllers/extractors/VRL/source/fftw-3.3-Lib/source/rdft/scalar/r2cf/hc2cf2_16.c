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
/* Generated on Sat Apr 28 11:03:31 EDT 2012 */

#include "codelet-rdft.h"

#ifdef HAVE_FMA

/* Generated by: ../../../genfft/gen_hc2c.native -fma -reorder-insns -schedule-for-pipeline -compact -variables 4 -pipeline-latency 4 -twiddle-log3 -precompute-twiddles -n 16 -dit -name hc2cf2_16 -include hc2cf.h */

/*
 * This function contains 196 FP additions, 134 FP multiplications,
 * (or, 104 additions, 42 multiplications, 92 fused multiply/add),
 * 100 stack variables, 3 constants, and 64 memory accesses
 */
#include "hc2cf.h"

static void hc2cf2_16(R *Rp, R *Ip, R *Rm, R *Im, const R *W, stride rs, INT mb, INT me, INT ms)
{
     DK(KP923879532, +0.923879532511286756128183189396788286822416626);
     DK(KP414213562, +0.414213562373095048801688724209698078569671875);
     DK(KP707106781, +0.707106781186547524400844362104849039284835938);
     {
	  INT m;
	  for (m = mb, W = W + ((mb - 1) * 8); m < me; m = m + 1, Rp = Rp + ms, Ip = Ip + ms, Rm = Rm - ms, Im = Im - ms, W = W + 8, MAKE_VOLATILE_STRIDE(rs)) {
	       E T3S, T3R;
	       {
		    E T2, Tf, TM, TO, T3, Tg, TN, TS, T4, Tp, T6, T5, Th;
		    T2 = W[0];
		    Tf = W[2];
		    TM = W[6];
		    TO = W[7];
		    T3 = W[4];
		    Tg = T2 * Tf;
		    TN = T2 * TM;
		    TS = T2 * TO;
		    T4 = T2 * T3;
		    Tp = Tf * T3;
		    T6 = W[5];
		    T5 = W[1];
		    Th = W[3];
		    {
			 E TZ, Te, T1U, T3A, T3L, T2D, T1G, T2B, T3h, T1R, T2w, T2I, T3i, Tx, T3M;
			 E T1Z, T3w, TL, T26, T25, T37, T1d, T2o, T2l, T3c, T1s, T2m, T2t, T3d, TX;
			 E T10, TV, T2a, TY, T2b;
			 {
			      E TF, TP, TT, Tq, TW, Tz, Tu, TI, TC, T1m, T1f, T1p, T1j, Tr, Ts;
			      E Tv, To, T1W;
			      {
				   E Ti, Tm, T1L, T1O, T1D, T1A, T1x, T2z, T1F, T2y;
				   {
					E T1, T7, Tb, T3z, T8, T1z, T9, Tc;
					{
					     E T1i, T1e, T1C, T1y, Tt, Ta, Tl;
					     T1 = Rp[0];
					     Tt = Tf * T6;
					     Ta = T2 * T6;
					     T7 = FMA(T5, T6, T4);
					     TF = FNMS(T5, T6, T4);
					     TP = FMA(T5, TO, TN);
					     TT = FNMS(T5, TM, TS);
					     Tq = FNMS(Th, T6, Tp);
					     TW = FMA(Th, T6, Tp);
					     Tz = FMA(T5, Th, Tg);
					     Ti = FNMS(T5, Th, Tg);
					     Tl = T2 * Th;
					     Tu = FMA(Th, T3, Tt);
					     TZ = FNMS(Th, T3, Tt);
					     TI = FMA(T5, T3, Ta);
					     Tb = FNMS(T5, T3, Ta);
					     T1i = Ti * T6;
					     T1e = Ti * T3;
					     T1C = Tz * T6;
					     T1y = Tz * T3;
					     Tm = FMA(T5, Tf, Tl);
					     TC = FNMS(T5, Tf, Tl);
					     T3z = Rm[0];
					     T8 = Rp[WS(rs, 4)];
					     T1m = FNMS(Tm, T6, T1e);
					     T1f = FMA(Tm, T6, T1e);
					     T1p = FMA(Tm, T3, T1i);
					     T1j = FNMS(Tm, T3, T1i);
					     T1L = FNMS(TC, T6, T1y);
					     T1z = FMA(TC, T6, T1y);
					     T1O = FMA(TC, T3, T1C);
					     T1D = FNMS(TC, T3, T1C);
					     T9 = T7 * T8;
					     Tc = Rm[WS(rs, 4)];
					}
					{
					     E T1u, T1w, T1v, T2x, T3y, T1B, T1E, Td, T3x;
					     T1u = Ip[WS(rs, 7)];
					     T1w = Im[WS(rs, 7)];
					     T1A = Ip[WS(rs, 3)];
					     Td = FMA(Tb, Tc, T9);
					     T3x = T7 * Tc;
					     T1v = TM * T1u;
					     T2x = TM * T1w;
					     Te = T1 + Td;
					     T1U = T1 - Td;
					     T3y = FNMS(Tb, T8, T3x);
					     T1B = T1z * T1A;
					     T1E = Im[WS(rs, 3)];
					     T1x = FMA(TO, T1w, T1v);
					     T3A = T3y + T3z;
					     T3L = T3z - T3y;
					     T2z = T1z * T1E;
					     T1F = FMA(T1D, T1E, T1B);
					     T2y = FNMS(TO, T1u, T2x);
					}
				   }
				   {
					E T1H, T1I, T1J, T1M, T1P, T2A;
					T1H = Ip[WS(rs, 1)];
					T2A = FNMS(T1D, T1A, T2z);
					T2D = T1x - T1F;
					T1G = T1x + T1F;
					T1I = Tf * T1H;
					T2B = T2y - T2A;
					T3h = T2y + T2A;
					T1J = Im[WS(rs, 1)];
					T1M = Ip[WS(rs, 5)];
					T1P = Im[WS(rs, 5)];
					{
					     E Tj, Tk, Tn, T1V;
					     {
						  E T1K, T2F, T1Q, T2H, T2E, T1N, T2G;
						  Tj = Rp[WS(rs, 2)];
						  T1K = FMA(Th, T1J, T1I);
						  T2E = Tf * T1J;
						  T1N = T1L * T1M;
						  T2G = T1L * T1P;
						  Tk = Ti * Tj;
						  T2F = FNMS(Th, T1H, T2E);
						  T1Q = FMA(T1O, T1P, T1N);
						  T2H = FNMS(T1O, T1M, T2G);
						  Tn = Rm[WS(rs, 2)];
						  Tr = Rp[WS(rs, 6)];
						  T1R = T1K + T1Q;
						  T2w = T1Q - T1K;
						  T2I = T2F - T2H;
						  T3i = T2F + T2H;
						  T1V = Ti * Tn;
						  Ts = Tq * Tr;
						  Tv = Rm[WS(rs, 6)];
					     }
					     To = FMA(Tm, Tn, Tk);
					     T1W = FNMS(Tm, Tj, T1V);
					}
				   }
			      }
			      {
				   E T19, T1b, T18, T2i, T1a, T2j;
				   {
					E TE, T22, TK, T24;
					{
					     E TA, TD, TB, T21, TG, TJ, TH, T23, T1Y, Tw, T1X;
					     TA = Rp[WS(rs, 1)];
					     Tw = FMA(Tu, Tv, Ts);
					     T1X = Tq * Tv;
					     TD = Rm[WS(rs, 1)];
					     TB = Tz * TA;
					     Tx = To + Tw;
					     T3M = To - Tw;
					     T1Y = FNMS(Tu, Tr, T1X);
					     T21 = Tz * TD;
					     TG = Rp[WS(rs, 5)];
					     TJ = Rm[WS(rs, 5)];
					     T1Z = T1W - T1Y;
					     T3w = T1W + T1Y;
					     TH = TF * TG;
					     T23 = TF * TJ;
					     TE = FMA(TC, TD, TB);
					     T22 = FNMS(TC, TA, T21);
					     TK = FMA(TI, TJ, TH);
					     T24 = FNMS(TI, TG, T23);
					}
					{
					     E T15, T17, T16, T2h;
					     T15 = Ip[0];
					     T17 = Im[0];
					     TL = TE + TK;
					     T26 = TE - TK;
					     T25 = T22 - T24;
					     T37 = T22 + T24;
					     T16 = T2 * T15;
					     T2h = T2 * T17;
					     T19 = Ip[WS(rs, 4)];
					     T1b = Im[WS(rs, 4)];
					     T18 = FMA(T5, T17, T16);
					     T2i = FNMS(T5, T15, T2h);
					     T1a = T3 * T19;
					     T2j = T3 * T1b;
					}
				   }
				   {
					E T1n, T1q, T1l, T2q, T1o, T2r;
					{
					     E T1g, T1k, T1h, T2p, T1c, T2k;
					     T1g = Ip[WS(rs, 2)];
					     T1k = Im[WS(rs, 2)];
					     T1c = FMA(T6, T1b, T1a);
					     T2k = FNMS(T6, T19, T2j);
					     T1h = T1f * T1g;
					     T2p = T1f * T1k;
					     T1d = T18 + T1c;
					     T2o = T18 - T1c;
					     T2l = T2i - T2k;
					     T3c = T2i + T2k;
					     T1n = Ip[WS(rs, 6)];
					     T1q = Im[WS(rs, 6)];
					     T1l = FMA(T1j, T1k, T1h);
					     T2q = FNMS(T1j, T1g, T2p);
					     T1o = T1m * T1n;
					     T2r = T1m * T1q;
					}
					{
					     E TQ, TU, TR, T29, T1r, T2s;
					     TQ = Rp[WS(rs, 7)];
					     TU = Rm[WS(rs, 7)];
					     T1r = FMA(T1p, T1q, T1o);
					     T2s = FNMS(T1p, T1n, T2r);
					     TR = TP * TQ;
					     T29 = TP * TU;
					     T1s = T1l + T1r;
					     T2m = T1l - T1r;
					     T2t = T2q - T2s;
					     T3d = T2q + T2s;
					     TX = Rp[WS(rs, 3)];
					     T10 = Rm[WS(rs, 3)];
					     TV = FMA(TT, TU, TR);
					     T2a = FNMS(TT, TQ, T29);
					     TY = TW * TX;
					     T2b = TW * T10;
					}
				   }
			      }
			 }
			 {
			      E T36, T3G, T3b, T3g, T28, T2d, T3F, T39, T3e, T3q, T3C, T3j, T3u, T3t;
			      {
				   E T3D, T1T, T3r, T14, T3E, T3s;
				   {
					E Ty, T3B, T11, T2c, T13, T3v;
					T36 = Te - Tx;
					Ty = Te + Tx;
					T3B = T3w + T3A;
					T3G = T3A - T3w;
					T11 = FMA(TZ, T10, TY);
					T2c = FNMS(TZ, TX, T2b);
					{
					     E T1t, T1S, T12, T38;
					     T3b = T1d - T1s;
					     T1t = T1d + T1s;
					     T1S = T1G + T1R;
					     T3g = T1G - T1R;
					     T12 = TV + T11;
					     T28 = TV - T11;
					     T2d = T2a - T2c;
					     T38 = T2a + T2c;
					     T3D = T1S - T1t;
					     T1T = T1t + T1S;
					     T13 = TL + T12;
					     T3F = T12 - TL;
					     T39 = T37 - T38;
					     T3v = T37 + T38;
					}
					T3e = T3c - T3d;
					T3r = T3c + T3d;
					T3q = Ty - T13;
					T14 = Ty + T13;
					T3E = T3B - T3v;
					T3C = T3v + T3B;
					T3s = T3h + T3i;
					T3j = T3h - T3i;
				   }
				   Rm[WS(rs, 7)] = T14 - T1T;
				   Rp[0] = T14 + T1T;
				   Im[WS(rs, 3)] = T3D - T3E;
				   T3u = T3r + T3s;
				   T3t = T3r - T3s;
				   Ip[WS(rs, 4)] = T3D + T3E;
			      }
			      {
				   E T3m, T3a, T3J, T3H;
				   Ip[0] = T3u + T3C;
				   Im[WS(rs, 7)] = T3u - T3C;
				   Rp[WS(rs, 4)] = T3q + T3t;
				   Rm[WS(rs, 3)] = T3q - T3t;
				   T3m = T36 - T39;
				   T3a = T36 + T39;
				   T3J = T3G - T3F;
				   T3H = T3F + T3G;
				   {
					E T2Q, T20, T3N, T3T, T2J, T2C, T3O, T2f, T34, T30, T2W, T2V, T3U, T2T, T2N;
					E T2v;
					{
					     E T2R, T27, T2e, T2S;
					     {
						  E T3n, T3f, T3o, T3k;
						  T2Q = T1U + T1Z;
						  T20 = T1U - T1Z;
						  T3n = T3e - T3b;
						  T3f = T3b + T3e;
						  T3o = T3g + T3j;
						  T3k = T3g - T3j;
						  T3N = T3L - T3M;
						  T3T = T3M + T3L;
						  {
						       E T3p, T3I, T3K, T3l;
						       T3p = T3n - T3o;
						       T3I = T3n + T3o;
						       T3K = T3k - T3f;
						       T3l = T3f + T3k;
						       Rp[WS(rs, 6)] = FMA(KP707106781, T3p, T3m);
						       Rm[WS(rs, 1)] = FNMS(KP707106781, T3p, T3m);
						       Ip[WS(rs, 2)] = FMA(KP707106781, T3I, T3H);
						       Im[WS(rs, 5)] = FMS(KP707106781, T3I, T3H);
						       Ip[WS(rs, 6)] = FMA(KP707106781, T3K, T3J);
						       Im[WS(rs, 1)] = FMS(KP707106781, T3K, T3J);
						       Rp[WS(rs, 2)] = FMA(KP707106781, T3l, T3a);
						       Rm[WS(rs, 5)] = FNMS(KP707106781, T3l, T3a);
						       T2R = T26 + T25;
						       T27 = T25 - T26;
						       T2e = T28 + T2d;
						       T2S = T28 - T2d;
						  }
					     }
					     {
						  E T2Y, T2Z, T2n, T2u;
						  T2J = T2D - T2I;
						  T2Y = T2D + T2I;
						  T2Z = T2B + T2w;
						  T2C = T2w - T2B;
						  T3O = T27 + T2e;
						  T2f = T27 - T2e;
						  T34 = FMA(KP414213562, T2Y, T2Z);
						  T30 = FNMS(KP414213562, T2Z, T2Y);
						  T2W = T2l - T2m;
						  T2n = T2l + T2m;
						  T2u = T2o - T2t;
						  T2V = T2o + T2t;
						  T3U = T2S - T2R;
						  T2T = T2R + T2S;
						  T2N = FNMS(KP414213562, T2n, T2u);
						  T2v = FMA(KP414213562, T2u, T2n);
					     }
					}
					{
					     E T33, T2X, T3X, T3Y;
					     {
						  E T2M, T2g, T2O, T2K, T3V, T3W, T2P, T2L;
						  T2M = FNMS(KP707106781, T2f, T20);
						  T2g = FMA(KP707106781, T2f, T20);
						  T33 = FNMS(KP414213562, T2V, T2W);
						  T2X = FMA(KP414213562, T2W, T2V);
						  T2O = FNMS(KP414213562, T2C, T2J);
						  T2K = FMA(KP414213562, T2J, T2C);
						  T3V = FMA(KP707106781, T3U, T3T);
						  T3X = FNMS(KP707106781, T3U, T3T);
						  T3W = T2O - T2N;
						  T2P = T2N + T2O;
						  T3Y = T2K - T2v;
						  T2L = T2v + T2K;
						  Ip[WS(rs, 3)] = FMA(KP923879532, T3W, T3V);
						  Im[WS(rs, 4)] = FMS(KP923879532, T3W, T3V);
						  Rp[WS(rs, 3)] = FMA(KP923879532, T2L, T2g);
						  Rm[WS(rs, 4)] = FNMS(KP923879532, T2L, T2g);
						  Rm[0] = FMA(KP923879532, T2P, T2M);
						  Rp[WS(rs, 7)] = FNMS(KP923879532, T2P, T2M);
					     }
					     {
						  E T32, T3P, T3Q, T35, T2U, T31;
						  T32 = FNMS(KP707106781, T2T, T2Q);
						  T2U = FMA(KP707106781, T2T, T2Q);
						  T31 = T2X + T30;
						  T3S = T30 - T2X;
						  T3R = FNMS(KP707106781, T3O, T3N);
						  T3P = FMA(KP707106781, T3O, T3N);
						  Ip[WS(rs, 7)] = FMA(KP923879532, T3Y, T3X);
						  Im[0] = FMS(KP923879532, T3Y, T3X);
						  Rp[WS(rs, 1)] = FMA(KP923879532, T31, T2U);
						  Rm[WS(rs, 6)] = FNMS(KP923879532, T31, T2U);
						  T3Q = T33 + T34;
						  T35 = T33 - T34;
						  Ip[WS(rs, 1)] = FMA(KP923879532, T3Q, T3P);
						  Im[WS(rs, 6)] = FMS(KP923879532, T3Q, T3P);
						  Rp[WS(rs, 5)] = FMA(KP923879532, T35, T32);
						  Rm[WS(rs, 2)] = FNMS(KP923879532, T35, T32);
					     }
					}
				   }
			      }
			 }
		    }
	       }
	       Ip[WS(rs, 5)] = FMA(KP923879532, T3S, T3R);
	       Im[WS(rs, 2)] = FMS(KP923879532, T3S, T3R);
	  }
     }
}

static const tw_instr twinstr[] = {
     {TW_CEXP, 1, 1},
     {TW_CEXP, 1, 3},
     {TW_CEXP, 1, 9},
     {TW_CEXP, 1, 15},
     {TW_NEXT, 1, 0}
};

static const hc2c_desc desc = { 16, "hc2cf2_16", twinstr, &GENUS, {104, 42, 92, 0} };

void X(codelet_hc2cf2_16) (planner *p) {
     X(khc2c_register) (p, hc2cf2_16, &desc, HC2C_VIA_RDFT);
}
#else				/* HAVE_FMA */

/* Generated by: ../../../genfft/gen_hc2c.native -compact -variables 4 -pipeline-latency 4 -twiddle-log3 -precompute-twiddles -n 16 -dit -name hc2cf2_16 -include hc2cf.h */

/*
 * This function contains 196 FP additions, 108 FP multiplications,
 * (or, 156 additions, 68 multiplications, 40 fused multiply/add),
 * 82 stack variables, 3 constants, and 64 memory accesses
 */
#include "hc2cf.h"

static void hc2cf2_16(R *Rp, R *Ip, R *Rm, R *Im, const R *W, stride rs, INT mb, INT me, INT ms)
{
     DK(KP382683432, +0.382683432365089771728459984030398866761344562);
     DK(KP923879532, +0.923879532511286756128183189396788286822416626);
     DK(KP707106781, +0.707106781186547524400844362104849039284835938);
     {
	  INT m;
	  for (m = mb, W = W + ((mb - 1) * 8); m < me; m = m + 1, Rp = Rp + ms, Ip = Ip + ms, Rm = Rm - ms, Im = Im - ms, W = W + 8, MAKE_VOLATILE_STRIDE(rs)) {
	       E T2, T5, Tg, Ti, Tk, To, TE, TC, T6, T3, T8, TW, TJ, Tt, TU;
	       E Tc, Tx, TH, TN, TO, TP, TR, T1f, T1k, T1b, T1i, T1y, T1H, T1u, T1F;
	       {
		    E T7, Tv, Ta, Ts, T4, Tw, Tb, Tr;
		    {
			 E Th, Tn, Tj, Tm;
			 T2 = W[0];
			 T5 = W[1];
			 Tg = W[2];
			 Ti = W[3];
			 Th = T2 * Tg;
			 Tn = T5 * Tg;
			 Tj = T5 * Ti;
			 Tm = T2 * Ti;
			 Tk = Th - Tj;
			 To = Tm + Tn;
			 TE = Tm - Tn;
			 TC = Th + Tj;
			 T6 = W[5];
			 T7 = T5 * T6;
			 Tv = Tg * T6;
			 Ta = T2 * T6;
			 Ts = Ti * T6;
			 T3 = W[4];
			 T4 = T2 * T3;
			 Tw = Ti * T3;
			 Tb = T5 * T3;
			 Tr = Tg * T3;
		    }
		    T8 = T4 + T7;
		    TW = Tv - Tw;
		    TJ = Ta + Tb;
		    Tt = Tr - Ts;
		    TU = Tr + Ts;
		    Tc = Ta - Tb;
		    Tx = Tv + Tw;
		    TH = T4 - T7;
		    TN = W[6];
		    TO = W[7];
		    TP = FMA(T2, TN, T5 * TO);
		    TR = FNMS(T5, TN, T2 * TO);
		    {
			 E T1d, T1e, T19, T1a;
			 T1d = Tk * T6;
			 T1e = To * T3;
			 T1f = T1d - T1e;
			 T1k = T1d + T1e;
			 T19 = Tk * T3;
			 T1a = To * T6;
			 T1b = T19 + T1a;
			 T1i = T19 - T1a;
		    }
		    {
			 E T1w, T1x, T1s, T1t;
			 T1w = TC * T6;
			 T1x = TE * T3;
			 T1y = T1w - T1x;
			 T1H = T1w + T1x;
			 T1s = TC * T3;
			 T1t = TE * T6;
			 T1u = T1s + T1t;
			 T1F = T1s - T1t;
		    }
	       }
	       {
		    E Tf, T3r, T1N, T3e, TA, T3s, T1Q, T3b, TM, T2M, T1W, T2w, TZ, T2N, T21;
		    E T2x, T1B, T1K, T2V, T2W, T2X, T2Y, T2j, T2D, T2o, T2E, T18, T1n, T2Q, T2R;
		    E T2S, T2T, T28, T2A, T2d, T2B;
		    {
			 E T1, T3d, Te, T3c, T9, Td;
			 T1 = Rp[0];
			 T3d = Rm[0];
			 T9 = Rp[WS(rs, 4)];
			 Td = Rm[WS(rs, 4)];
			 Te = FMA(T8, T9, Tc * Td);
			 T3c = FNMS(Tc, T9, T8 * Td);
			 Tf = T1 + Te;
			 T3r = T3d - T3c;
			 T1N = T1 - Te;
			 T3e = T3c + T3d;
		    }
		    {
			 E Tq, T1O, Tz, T1P;
			 {
			      E Tl, Tp, Tu, Ty;
			      Tl = Rp[WS(rs, 2)];
			      Tp = Rm[WS(rs, 2)];
			      Tq = FMA(Tk, Tl, To * Tp);
			      T1O = FNMS(To, Tl, Tk * Tp);
			      Tu = Rp[WS(rs, 6)];
			      Ty = Rm[WS(rs, 6)];
			      Tz = FMA(Tt, Tu, Tx * Ty);
			      T1P = FNMS(Tx, Tu, Tt * Ty);
			 }
			 TA = Tq + Tz;
			 T3s = Tq - Tz;
			 T1Q = T1O - T1P;
			 T3b = T1O + T1P;
		    }
		    {
			 E TG, T1S, TL, T1T, T1U, T1V;
			 {
			      E TD, TF, TI, TK;
			      TD = Rp[WS(rs, 1)];
			      TF = Rm[WS(rs, 1)];
			      TG = FMA(TC, TD, TE * TF);
			      T1S = FNMS(TE, TD, TC * TF);
			      TI = Rp[WS(rs, 5)];
			      TK = Rm[WS(rs, 5)];
			      TL = FMA(TH, TI, TJ * TK);
			      T1T = FNMS(TJ, TI, TH * TK);
			 }
			 TM = TG + TL;
			 T2M = T1S + T1T;
			 T1U = T1S - T1T;
			 T1V = TG - TL;
			 T1W = T1U - T1V;
			 T2w = T1V + T1U;
		    }
		    {
			 E TT, T1Y, TY, T1Z, T1X, T20;
			 {
			      E TQ, TS, TV, TX;
			      TQ = Rp[WS(rs, 7)];
			      TS = Rm[WS(rs, 7)];
			      TT = FMA(TP, TQ, TR * TS);
			      T1Y = FNMS(TR, TQ, TP * TS);
			      TV = Rp[WS(rs, 3)];
			      TX = Rm[WS(rs, 3)];
			      TY = FMA(TU, TV, TW * TX);
			      T1Z = FNMS(TW, TV, TU * TX);
			 }
			 TZ = TT + TY;
			 T2N = T1Y + T1Z;
			 T1X = TT - TY;
			 T20 = T1Y - T1Z;
			 T21 = T1X + T20;
			 T2x = T1X - T20;
		    }
		    {
			 E T1r, T2k, T1J, T2h, T1A, T2l, T1E, T2g;
			 {
			      E T1p, T1q, T1G, T1I;
			      T1p = Ip[WS(rs, 7)];
			      T1q = Im[WS(rs, 7)];
			      T1r = FMA(TN, T1p, TO * T1q);
			      T2k = FNMS(TO, T1p, TN * T1q);
			      T1G = Ip[WS(rs, 5)];
			      T1I = Im[WS(rs, 5)];
			      T1J = FMA(T1F, T1G, T1H * T1I);
			      T2h = FNMS(T1H, T1G, T1F * T1I);
			 }
			 {
			      E T1v, T1z, T1C, T1D;
			      T1v = Ip[WS(rs, 3)];
			      T1z = Im[WS(rs, 3)];
			      T1A = FMA(T1u, T1v, T1y * T1z);
			      T2l = FNMS(T1y, T1v, T1u * T1z);
			      T1C = Ip[WS(rs, 1)];
			      T1D = Im[WS(rs, 1)];
			      T1E = FMA(Tg, T1C, Ti * T1D);
			      T2g = FNMS(Ti, T1C, Tg * T1D);
			 }
			 T1B = T1r + T1A;
			 T1K = T1E + T1J;
			 T2V = T1B - T1K;
			 T2W = T2k + T2l;
			 T2X = T2g + T2h;
			 T2Y = T2W - T2X;
			 {
			      E T2f, T2i, T2m, T2n;
			      T2f = T1r - T1A;
			      T2i = T2g - T2h;
			      T2j = T2f - T2i;
			      T2D = T2f + T2i;
			      T2m = T2k - T2l;
			      T2n = T1E - T1J;
			      T2o = T2m + T2n;
			      T2E = T2m - T2n;
			 }
		    }
		    {
			 E T14, T24, T1m, T2b, T17, T25, T1h, T2a;
			 {
			      E T12, T13, T1j, T1l;
			      T12 = Ip[0];
			      T13 = Im[0];
			      T14 = FMA(T2, T12, T5 * T13);
			      T24 = FNMS(T5, T12, T2 * T13);
			      T1j = Ip[WS(rs, 6)];
			      T1l = Im[WS(rs, 6)];
			      T1m = FMA(T1i, T1j, T1k * T1l);
			      T2b = FNMS(T1k, T1j, T1i * T1l);
			 }
			 {
			      E T15, T16, T1c, T1g;
			      T15 = Ip[WS(rs, 4)];
			      T16 = Im[WS(rs, 4)];
			      T17 = FMA(T3, T15, T6 * T16);
			      T25 = FNMS(T6, T15, T3 * T16);
			      T1c = Ip[WS(rs, 2)];
			      T1g = Im[WS(rs, 2)];
			      T1h = FMA(T1b, T1c, T1f * T1g);
			      T2a = FNMS(T1f, T1c, T1b * T1g);
			 }
			 T18 = T14 + T17;
			 T1n = T1h + T1m;
			 T2Q = T18 - T1n;
			 T2R = T24 + T25;
			 T2S = T2a + T2b;
			 T2T = T2R - T2S;
			 {
			      E T26, T27, T29, T2c;
			      T26 = T24 - T25;
			      T27 = T1h - T1m;
			      T28 = T26 + T27;
			      T2A = T26 - T27;
			      T29 = T14 - T17;
			      T2c = T2a - T2b;
			      T2d = T29 - T2c;
			      T2B = T29 + T2c;
			 }
		    }
		    {
			 E T23, T2r, T3A, T3C, T2q, T3B, T2u, T3x;
			 {
			      E T1R, T22, T3y, T3z;
			      T1R = T1N - T1Q;
			      T22 = KP707106781 * (T1W - T21);
			      T23 = T1R + T22;
			      T2r = T1R - T22;
			      T3y = KP707106781 * (T2x - T2w);
			      T3z = T3s + T3r;
			      T3A = T3y + T3z;
			      T3C = T3z - T3y;
			 }
			 {
			      E T2e, T2p, T2s, T2t;
			      T2e = FMA(KP923879532, T28, KP382683432 * T2d);
			      T2p = FNMS(KP923879532, T2o, KP382683432 * T2j);
			      T2q = T2e + T2p;
			      T3B = T2p - T2e;
			      T2s = FNMS(KP923879532, T2d, KP382683432 * T28);
			      T2t = FMA(KP382683432, T2o, KP923879532 * T2j);
			      T2u = T2s - T2t;
			      T3x = T2s + T2t;
			 }
			 Rm[WS(rs, 4)] = T23 - T2q;
			 Im[WS(rs, 4)] = T3x - T3A;
			 Rp[WS(rs, 3)] = T23 + T2q;
			 Ip[WS(rs, 3)] = T3x + T3A;
			 Rm[0] = T2r - T2u;
			 Im[0] = T3B - T3C;
			 Rp[WS(rs, 7)] = T2r + T2u;
			 Ip[WS(rs, 7)] = T3B + T3C;
		    }
		    {
			 E T2P, T31, T3m, T3o, T30, T3n, T34, T3j;
			 {
			      E T2L, T2O, T3k, T3l;
			      T2L = Tf - TA;
			      T2O = T2M - T2N;
			      T2P = T2L + T2O;
			      T31 = T2L - T2O;
			      T3k = TZ - TM;
			      T3l = T3e - T3b;
			      T3m = T3k + T3l;
			      T3o = T3l - T3k;
			 }
			 {
			      E T2U, T2Z, T32, T33;
			      T2U = T2Q + T2T;
			      T2Z = T2V - T2Y;
			      T30 = KP707106781 * (T2U + T2Z);
			      T3n = KP707106781 * (T2Z - T2U);
			      T32 = T2T - T2Q;
			      T33 = T2V + T2Y;
			      T34 = KP707106781 * (T32 - T33);
			      T3j = KP707106781 * (T32 + T33);
			 }
			 Rm[WS(rs, 5)] = T2P - T30;
			 Im[WS(rs, 5)] = T3j - T3m;
			 Rp[WS(rs, 2)] = T2P + T30;
			 Ip[WS(rs, 2)] = T3j + T3m;
			 Rm[WS(rs, 1)] = T31 - T34;
			 Im[WS(rs, 1)] = T3n - T3o;
			 Rp[WS(rs, 6)] = T31 + T34;
			 Ip[WS(rs, 6)] = T3n + T3o;
		    }
		    {
			 E T2z, T2H, T3u, T3w, T2G, T3v, T2K, T3p;
			 {
			      E T2v, T2y, T3q, T3t;
			      T2v = T1N + T1Q;
			      T2y = KP707106781 * (T2w + T2x);
			      T2z = T2v + T2y;
			      T2H = T2v - T2y;
			      T3q = KP707106781 * (T1W + T21);
			      T3t = T3r - T3s;
			      T3u = T3q + T3t;
			      T3w = T3t - T3q;
			 }
			 {
			      E T2C, T2F, T2I, T2J;
			      T2C = FMA(KP382683432, T2A, KP923879532 * T2B);
			      T2F = FNMS(KP382683432, T2E, KP923879532 * T2D);
			      T2G = T2C + T2F;
			      T3v = T2F - T2C;
			      T2I = FNMS(KP382683432, T2B, KP923879532 * T2A);
			      T2J = FMA(KP923879532, T2E, KP382683432 * T2D);
			      T2K = T2I - T2J;
			      T3p = T2I + T2J;
			 }
			 Rm[WS(rs, 6)] = T2z - T2G;
			 Im[WS(rs, 6)] = T3p - T3u;
			 Rp[WS(rs, 1)] = T2z + T2G;
			 Ip[WS(rs, 1)] = T3p + T3u;
			 Rm[WS(rs, 2)] = T2H - T2K;
			 Im[WS(rs, 2)] = T3v - T3w;
			 Rp[WS(rs, 5)] = T2H + T2K;
			 Ip[WS(rs, 5)] = T3v + T3w;
		    }
		    {
			 E T11, T35, T3g, T3i, T1M, T3h, T38, T39;
			 {
			      E TB, T10, T3a, T3f;
			      TB = Tf + TA;
			      T10 = TM + TZ;
			      T11 = TB + T10;
			      T35 = TB - T10;
			      T3a = T2M + T2N;
			      T3f = T3b + T3e;
			      T3g = T3a + T3f;
			      T3i = T3f - T3a;
			 }
			 {
			      E T1o, T1L, T36, T37;
			      T1o = T18 + T1n;
			      T1L = T1B + T1K;
			      T1M = T1o + T1L;
			      T3h = T1L - T1o;
			      T36 = T2R + T2S;
			      T37 = T2W + T2X;
			      T38 = T36 - T37;
			      T39 = T36 + T37;
			 }
			 Rm[WS(rs, 7)] = T11 - T1M;
			 Im[WS(rs, 7)] = T39 - T3g;
			 Rp[0] = T11 + T1M;
			 Ip[0] = T39 + T3g;
			 Rm[WS(rs, 3)] = T35 - T38;
			 Im[WS(rs, 3)] = T3h - T3i;
			 Rp[WS(rs, 4)] = T35 + T38;
			 Ip[WS(rs, 4)] = T3h + T3i;
		    }
	       }
	  }
     }
}

static const tw_instr twinstr[] = {
     {TW_CEXP, 1, 1},
     {TW_CEXP, 1, 3},
     {TW_CEXP, 1, 9},
     {TW_CEXP, 1, 15},
     {TW_NEXT, 1, 0}
};

static const hc2c_desc desc = { 16, "hc2cf2_16", twinstr, &GENUS, {156, 68, 40, 0} };

void X(codelet_hc2cf2_16) (planner *p) {
     X(khc2c_register) (p, hc2cf2_16, &desc, HC2C_VIA_RDFT);
}
#endif				/* HAVE_FMA */

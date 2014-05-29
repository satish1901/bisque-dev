/*******************************************************************************

@author John Delaney


*******************************************************************************/

/*
LICENSE

Center for Bio-Image Informatics, University of California at Santa Barbara

Copyright (c) 2007-2014 by the Regents of the University of California
All rights reserved

Redistribution and use in source and binary forms, in whole or in parts, with or without
modification, are permitted provided that the following conditions are met:

    Redistributions of source code must retain the above copyright
    notice, this list of conditions, and the following disclaimer.

    Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions, and the following disclaimer in
    the documentation and/or other materials provided with the
    distribution.

    Use or redistribution must display the attribution with the logo
    or project name and the project URL link in a location commonly
    visible by the end users, unless specifically permitted by the 
    license holders.

THIS SOFTWARE IS PROVIDED BY THE REGENTS OF THE UNIVERSITY OF CALIFORNIA ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE REGENTS OF THE UNIVERSITY OF CALIFORNIA OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
*/


#ifdef GL_ES
precision highp float;
#endif

#define M_PI 3.14159265358979323846

#define LIGHTING 0
#define PHONG 0

uniform vec2 iResolution;

uniform vec3 BOX_SIZE;

uniform int setMaxSteps;

uniform int RED_CHANNEL;
uniform int GREEN_CHANNEL;
uniform int BLUE_CHANNEL;

uniform int   DITHERING;
uniform int   DITHER_SPACE;
uniform int   DITHER_LIGHTING;

//uniform int   LIGHTING;
uniform int   LIGHT_SAMPLES;
uniform float LIGHT_DEPTH;
uniform float LIGHT_SIG;
uniform vec3 LIGHT_POSITION;

uniform float DISP_SIG;
uniform float DISPERSION;

uniform int   NORMAL_MULT;
uniform float KA;
uniform float KD;
uniform float NORMAL_INTENSITY;
uniform float SPEC_SIZE;
uniform float SPEC_INTENSITY;

uniform float GAMMA_MIN;
uniform float GAMMA_MAX;
uniform float GAMMA_SCALE;
uniform float brightness;
uniform float density;

//uniform sampler2D backGround;

uniform sampler2D dataBase0[1];
//uniform sampler2D dataBase1[1];

uniform int TEX_RES_X;
uniform int TEX_RES_Y;
uniform int ATLAS_X;
uniform int ATLAS_Y;
uniform int SLICES;
uniform int RES_X;
uniform int RES_Y;
uniform int RES_Z;

uniform float CLIP_NEAR;
uniform float CLIP_FAR;

vec4 luma2Alpha(vec4 color, float min, float max, float C){
  float x = sqrt(color[0]*color[0] +color[1]*color[1] +color[2]*color[2]);
  //float x = color[0] + color[1] + color[2];
  float xi = (x-min)/(max-min);
  float y = pow(xi,C);
  y = clamp(y,0.0,1.0);
  color[3] = y;
  return(color);
}

vec4 channel(vec4 smp){
  vec4 col = vec4(float(RED_CHANNEL)*smp[0],
                  float(GREEN_CHANNEL)*smp[1],
                  float(BLUE_CHANNEL)*smp[2],0.0);
  return col;
}

vec2 offsetBackFront(float t, float nx){
  vec2 os = vec2((1.0-mod(t,1.0))*nx-1.0, floor(t));
  return os;
}

vec2 offsetFrontBack(float t, float nx, float ny){
  vec2 os = vec2((mod(t,1.0))*nx, ny - floor(t) - 1.0);
  return os;
}


vec4 sampleAs3DTexture(sampler2D tex, vec4 pos) {
  //vec4 pos = -0.5*(texCoord - 1.0);
  //pos[0] = 1.0 - pos[0];
  //pos[1] = 1.0 - pos[1];
  //pos[2] = 1.0 - pos[2];
  //return pos;
  //vec4 pos = 0.5*(1.0 - texCoord);
  //return vec4(pos.xyz,0.05);
  pos = clamp(pos,vec4(-0.999),vec4(0.999));
  for(int i = 0; i < 3; i++){

  }


  float nx      = float(ATLAS_X);
  float ny      = float(ATLAS_Y);
  float nSlices = float(SLICES);
  float sx      = float(TEX_RES_X);
  float sy      = float(TEX_RES_Y);

  vec2 loc = vec2(pos.x/nx,pos.y/ny);
  loc[1] = 1.0/ny - loc[1];

  vec2 pix = vec2(1.0/nx,1.0/ny);

  float iz = pos.z*nSlices;
  float zs = floor(iz);
  float ty  = zs/nx;
  float typ = (zs+1.0)/nx;

  typ = clamp(typ, 0.0, nSlices);
  vec2 o0 = offsetFrontBack(ty,nx,ny)*pix;
  vec2 o1 = offsetFrontBack(typ,nx,ny)*pix;

  //return vec4(o0/vec2(nx,ny),0.0,0.5);

  float t = mod(iz, 1.0);
  vec4 slice0Color = texture2D(tex, loc + o0);
  vec4 slice1Color = texture2D(tex, loc + o1);

  return mix(slice0Color, slice1Color, t);
}



vec4 sampleBlocks(sampler2D dataBase0[1], vec4 texCoord, ivec4 nBlocks) {


  texCoord = clamp(texCoord,vec4(-0.999),vec4(0.999));
  vec4 pos = 0.5*(1.0 - texCoord);
  pos[0] = 1.0 - pos[0];

  vec4 nBlocksf = vec4(nBlocks);
  vec4  blockf  = pos*nBlocksf;
  vec4  blockif = vec4(floor(blockf));
  ivec4 blocki  = ivec4(blockif);
  int blockInd = blocki[0] + blocki[1]*nBlocks[0] + blocki[2]*nBlocks[0]*nBlocks[1];

  vec4 blockPos = blockf - vec4(blocki);
  //return blockPos;
  float nx      = float(ATLAS_X);
  float ny      = float(ATLAS_Y);
  float nSlices = float(SLICES);
  float sx      = float(TEX_RES_X);
  float sy      = float(TEX_RES_Y);
  vec4 imgRes = vec4(sx,sy,nSlices,1.0);
  vec4 imgPos = blockPos*imgRes;

  if(blockInd == 0) return sampleAs3DTexture(dataBase0[0],blockPos);
#if 0
  if(blockInd == 1) return sampleAs3DTexture(dataBase0[1],blockPos);
  if(blockInd == 2) return sampleAs3DTexture(dataBase0[2],blockPos);
  if(blockInd == 3) return sampleAs3DTexture(dataBase0[3],blockPos);
  if(blockInd == 4) return sampleAs3DTexture(dataBase0[4],blockPos);
  if(blockInd == 5) return sampleAs3DTexture(dataBase0[5],blockPos);
  if(blockInd == 6) return sampleAs3DTexture(dataBase0[6],blockPos);
  if(blockInd == 7) return sampleAs3DTexture(dataBase0[7],blockPos);

  if(blockInd == 8) return sampleAs3DTexture(dataBase1[0],blockPos);
  if(blockInd == 9) return sampleAs3DTexture(dataBase1[1],blockPos);
  if(blockInd == 10) return sampleAs3DTexture(dataBase1[2],blockPos);
  if(blockInd == 11) return sampleAs3DTexture(dataBase1[3],blockPos);
  if(blockInd == 12) return sampleAs3DTexture(dataBase1[4],blockPos);
  if(blockInd == 13) return sampleAs3DTexture(dataBase1[5],blockPos);
  if(blockInd == 14) return sampleAs3DTexture(dataBase1[6],blockPos);
  if(blockInd == 15) return sampleAs3DTexture(dataBase1[7],blockPos);
#endif

  return vec4(0.0);
}


float rand(vec2 co){
  return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

vec4 getNormal(sampler2D tex[1], vec4 texCoord, ivec4 nBlocks){
  float nx      = float(ATLAS_X);
  float ny      = float(ATLAS_Y);
  /*
    float rx = rand(texCoord.xy);
    float ry = rand(texCoord.zy);
    float rz = rand(texCoord.xz);
    rx = clamp(rx, 0.25, 1.0);
    ry = clamp(rx, 0.25, 1.0);
    rz = clamp(rx, 0.25, 1.0);
  */
  float nSlices = float(SLICES);
  float sx      = float(TEX_RES_X);
  float sy      = float(TEX_RES_Y);

  float v0 = length(sampleBlocks(tex, texCoord + vec4(1.0/sx, 0.    ,  0., 0.),nBlocks));
  float v1 = length(sampleBlocks(tex, texCoord - vec4(1.0/sx, 0.    ,  0., 0.),nBlocks));
  float v2 = length(sampleBlocks(tex, texCoord + vec4(0.,     1.0/sx,  0., 0.),nBlocks));
  float v3 = length(sampleBlocks(tex, texCoord - vec4(0.,     1.0/sy,  0., 0.),nBlocks));
  float v4 = length(sampleBlocks(tex, texCoord + vec4(0., 0., 1.0/nSlices, 0.),nBlocks));
  float v5 = length(sampleBlocks(tex, texCoord - vec4(0., 0., 1.0/nSlices, 0.),nBlocks));
  vec3 grad = -vec3((v0-v1),(v2-v3),(v4-v5));

  /*
    vec4 v40 = sampleBlocks(tex, texCoord + vec4(1.0/sx, 0.    ,  0., 0.),nBlocks);
    vec4 v41 = sampleBlocks(tex, texCoord - vec4(1.0/sx, 0.    ,  0., 0.),nBlocks);
    vec4 v42 = sampleBlocks(tex, texCoord + vec4(0.,     1.0/sx,  0., 0.),nBlocks);
    vec4 v43 = sampleBlocks(tex, texCoord - vec4(0.,     1.0/sy,  0., 0.),nBlocks);
    vec4 v44 = sampleBlocks(tex, texCoord + vec4(0., 0., 1.0/nSlices, 0.),nBlocks);
    vec4 v45 = sampleBlocks(tex, texCoord - vec4(0., 0., 1.0/nSlices, 0.),nBlocks);
    float vx = length(v40 - v41);
    float vy = length(v43 - v43);
    float vz = length(v44 - v45);
    vec3 grad = -vec3(vx,vy,vz);
  */
  float a =  length(grad);
  if(a < 1e-9)
    return vec4(0.0);
  else
    return vec4(normalize(grad),a);
  //return grad;
}

bool intersectBox(in vec4 r_o, in vec4 r_d, in vec4 boxmin, in vec4 boxmax,
                  out float tnear, out float tfar)
{
  // compute intersection of ray with all six bbox planes
  vec4 invR = vec4(1.0,1.0,1.0,0.0) / r_d;
  vec4 tbot = invR * (boxmin - r_o);
  vec4 ttop = invR * (boxmax - r_o);

  // re-order intersections to find smallest and largest on each axis
  vec4 tmin = min(ttop, tbot);
  vec4 tmax = max(ttop, tbot);

  // find the largest tmin and the smallest tmax
  float largest_tmin  = max(max(tmin.x, tmin.y), max(tmin.x, tmin.z));
  float smallest_tmax = min(min(tmax.x, tmax.y), min(tmax.x, tmax.z));

  tnear = largest_tmin;
  tfar = smallest_tmax;

  return(smallest_tmax > largest_tmin);
}


//float turb(vec3 x){
//  float t =
//    snoise(256.0*x)*.375 + snoise(128.0*x)*.125;
//  t += 0.5*(0.5 - rand(x.xy));
//  return 1.25*t;
//}

vec4 integrateVolume(vec4 eye_o,vec4 eye_d,
                     vec4 boxMin, vec4 boxMax,vec4 boxScale,
                     sampler2D dataBase0[1],
                     //sampler2D dataBase1[1],
                     ivec4 nBlocks){
  float tnear, tfar;
  bool hit = intersectBox(eye_o, eye_d, boxMin, boxMax, tnear,  tfar);


  if (!hit || tnear > CLIP_FAR || tfar < CLIP_NEAR) {
    return vec4(0.5);
  }

  // march along ray from back to front, accumulating color
  const int maxSteps = 512;
  float csteps = float(setMaxSteps);
  csteps = clamp(csteps,0.0,float(maxSteps));
  float isteps = 1.0/csteps;

  float tstep = 0.3*isteps;

  float tbegin = tfar;
  float tend   = tnear;

  float tfarsurf = CLIP_FAR; // choose some arbitrarily far surface
  float overflow = (tfarsurf - tfar)/tstep;
  overflow -= floor(overflow);
  float r = 1.0*rand(eye_d.xy);

  float t = tbegin + (overflow)*tstep;
  t = clamp(t, 0.0, CLIP_FAR);
  t += float(DITHERING)*r*tstep;

  vec4 C = vec4(0.0);
  C+= vec4(0.5);

  float A = 0.0;
  float     tdist    = 0.0;
  const int maxStepsLight = 32;

  float lstep = LIGHT_DEPTH/float(LIGHT_SAMPLES);
  float absorption = 1.;
  vec4 lightPos = vec4(LIGHT_POSITION,.0);

  float T = 1.0;
  int numSteps = 0;
  for(int i=0; i<maxSteps; i++){

    vec4 pos = (eye_o + eye_d*t)/boxScale; // map position to [0, 1] coordinates
    vec4 smp = sampleBlocks(dataBase0,pos,nBlocks);
    vec4 col = luma2Alpha(smp, GAMMA_MIN, GAMMA_MAX, GAMMA_SCALE);
    //col = vec4(col[3]);
    vec4 dl = lightPos - pos;
#if PHONG
    vec4 N = getNormal(dataBase0,pos,nBlocks);
    float lum = N[3];

    dl = normalize(dl);
    vec4 V = -normalize(eye_d);
    vec4 H = dl + V;
    H = normalize(H);
    float lightVal = dot(dl.xyz, N.xyz);
    float spec = pow(1.1*dot( N.xyz, H.xyz ),SPEC_SIZE);
    spec = clamp(spec, 0.0, spec);
    // += vec4(vec3(spec),0.0);

    float kn = pow(10.0*N[3],1.0*NORMAL_INTENSITY);
    float ka = KA;
    float kd = KD;
    float ks = SPEC_INTENSITY;
    kn = clamp(kn,0.0,1.0);
    //float kn = 1.0;
    col *= (ka + kd*vec4(vec3(lightVal),kn));
    col +=  ks*N[3]*vec4(spec);
    col = clamp(col, 0.0, 1.0);
    //col = N;
#endif

#if LIGHTING

    float Dl = 0.0;

    vec3 DISP_BIAS = vec3(100.5, 200.3, 0.004);
    dl = normalize(dl);
    vec3 dtemp = cross(dl.xyz,vec3(1.0,1.0,1.0)); dtemp = normalize(dtemp);
    vec3 N1 = cross(dl.xyz,dtemp);
    vec3 N2 = cross(dl.xyz,N1);
    N1 = normalize(N1);
    N2 = normalize(N2);
    //float r0 = 0.1*rand(pos.xy + eye_d.xz);
    float r1 = 1.0 - 2.0*rand(pos.yz + eye_d.zx);
    float r2 = 1.0 - 2.0*rand(pos.xz + eye_d.yx);
    for(int j=0; j<maxStepsLight; j++){ //*/
      if (j > LIGHT_SAMPLES) break;

      float lti = (float(j))*lstep;
      vec3 Ni   = DISPERSION*normalize(r1*N1 + r2*N2);
      vec4 lpos = pos + lti*normalize(dl + vec4(Ni,0.0));

      vec4 dsmp = sampleBlocks(dataBase0,lpos,nBlocks);
      vec4 dens = luma2Alpha(dsmp, GAMMA_MIN, GAMMA_MAX, GAMMA_SCALE);
      float Kdisp = DISP_SIG;
      float sl = float(maxStepsLight)/float(LIGHT_SAMPLES);
      dens.w *= 1.0*density;
      dens.w = 1.0 - pow(1.0-dens.w/DISP_SIG,sl);
      dens.w = clamp(dens.w, 0.0, 1.0);
      Dl =  (1.0-dens.w)*Dl + dens.w;
    }
    col *= (1.0 - exp(-Dl));
    col.xyz *= 1.0 - Dl;
    col.xyz *= 100.0*brightness;
#else
    col.xyz *= brightness;
#endif
    float s = float(maxSteps)/float(setMaxSteps);
   
    col.w *= density;
    col.w = 1.0 - pow((1.0-col.w),s);

    col.xyz *= col.w;

    C = (1.0-col.w)*C + col;

    t -= tstep;
    numSteps = i;
    if (i > setMaxSteps || t  < tend || t < CLIP_NEAR) break;
  }


  //if(!over) C += (1.0-C.w)*vec4(0.5);
  return C;
}

void getRay(in vec2 screen, in vec2 res,
            out vec4 eo, out vec4 ed){
  vec4 eyeRay_d;
  ed.xy = 2.0*screen.xy/res.xy - 1.0;
  ed[0] *= iResolution.x/iResolution.y;

  //gl_FragColor = vec4(rand(gl_FragCoord.xy));
  //if(gl_FragCoord.x/iResolution.x/1.25 > 1.0)   gl_FragColor = vec4(1.0,0.0,0.,0.);
  //if(gl_FragCoord.y/iResolution.y/1.25 > 1.0)   gl_FragColor = vec4(0.0,1.0,0.,0.);
  //return;

  float fovr = 20.*M_PI/180.;
  ed[2] = -1.0/tan(fovr*0.5);
  ed   = ed*viewMatrix;
  ed[3] = 0.0;
  //ed = normalize(ed);
  eo = vec4(cameraPosition,1.0);
}


void main()
{
  vec4 eyeRay_d, eyeRay_o;
  vec2 fragCoord = gl_FragCoord.xy;


  getRay(fragCoord, iResolution.xy, eyeRay_o, eyeRay_d);
  vec4 boxMin = vec4(-1.0);
  vec4 boxMax = vec4( 1.0);
  vec4 boxTrans = vec4(0.0, 0.0, 0.0, 0.0);
  vec4 boxScale = vec4(BOX_SIZE,1.0);

  boxMin *= boxScale;
  boxMax *= boxScale;
  //boxMin += boxTrans;
  //boxMax += boxTrans;
  ivec4 nBlocks = ivec4(RES_X,RES_Y,RES_Z,1);

  vec4 C = integrateVolume(eyeRay_o, eyeRay_d,
                           boxMin, boxMax, boxScale,
                           dataBase0,nBlocks);
  gl_FragColor = C;
  return;

  //C *= brightness;
  //vec4 diff = vec4(vec3(0.5),0.0);
  //C += diff;

#if 0
  if ((gl_FragCoord[0] < 1.25*iResolution[0]) && (gl_FragCoord[1] < 1.25*iResolution[1])) {
    // write output color
    //C = clamp(C,0,1.0);
    gl_FragColor = C;
    //gl_FragColor = vec4(1.0-C[3]);
    //gl_FragColor = (eyeRay_o + eyeRay_d*t)/boxScale; // map position to [0, 1] coordinates
    //gl_FragColor = vec4(t/30.0);
    //gl_FragColor = eyeRay_d;
    //gl_FragColor = C + (1.0-C[3]*density)*vec4(vec3(0.75),0.0);
    //gl_FragColor = 0.1*vec4(t-tnear);
  }
#endif

}

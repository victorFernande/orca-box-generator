/* Render actual Box mesh arrays with a depth buffer, without triangle sorting.
 * Copyright (c) 2026 Orca Box Studio (MIT; see LICENSE).
 * Development-only tool: JSON scene on stdin, transparent PNG path on argv[2].
 */
const fs = require('fs');
const path = require('path');
const {chromium} = require(process.env.ORCA_PLAYWRIGHT_MODULE || 'playwright');

(async()=>{
  const scene=JSON.parse(fs.readFileSync(0,'utf8'));
  const destination=path.resolve(process.argv[2]);
  const browser=await chromium.launch({headless:true,args:['--use-angle=swiftshader','--enable-webgl','--ignore-gpu-blocklist','--enable-unsafe-swiftshader'],...(process.env.ORCA_CHROMIUM_PATH?{executablePath:process.env.ORCA_CHROMIUM_PATH}:{})});
  try{
    const page=await browser.newPage({viewport:{width:scene.width,height:scene.height},deviceScaleFactor:1});
    await page.setContent('<!doctype html><style>html,body{margin:0;background:transparent;overflow:hidden}canvas{display:block}</style><canvas id="model"></canvas>');
    const report=await page.evaluate(data=>{
      const canvas=document.querySelector('#model');canvas.width=data.width;canvas.height=data.height;
      const gl=canvas.getContext('webgl2',{alpha:true,antialias:true,preserveDrawingBuffer:true,premultipliedAlpha:false});
      if(!gl)throw Error('WebGL2 unavailable for model rendering');
      const shader=(type,source)=>{const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;};
      const program=gl.createProgram();
      gl.attachShader(program,shader(gl.VERTEX_SHADER,`#version 300 es
        precision highp float;
        layout(location=0) in vec3 position;
        layout(location=1) in vec3 normal;
        layout(location=2) in vec3 colour;
        out vec3 surfaceColour; out vec3 surfaceNormal;
        void main(){gl_Position=vec4(position,1.0);surfaceColour=colour;surfaceNormal=normal;}`));
      gl.attachShader(program,shader(gl.FRAGMENT_SHADER,`#version 300 es
        precision highp float;
        in vec3 surfaceColour; in vec3 surfaceNormal; out vec4 fragment;
        void main(){vec3 n=normalize(surfaceNormal);vec3 light=normalize(vec3(-0.35,-0.45,1.0));
          float diffuse=max(0.0,dot(n,light));float ambient=0.40+0.08*max(0.0,n.z);
          fragment=vec4(surfaceColour*(ambient+0.52*diffuse),1.0);}`));
      gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));gl.useProgram(program);
      const az=data.azimuth*Math.PI/180,al=data.altitude*Math.PI/180;
      const right=[-Math.sin(az),Math.cos(az),0],camera=[Math.cos(az)*Math.cos(al),Math.sin(az)*Math.cos(al),Math.sin(al)];
      const up=[camera[1]*right[2]-camera[2]*right[1],camera[2]*right[0]-camera[0]*right[2],camera[0]*right[1]-camera[1]*right[0]];
      const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
      const projected=data.vertices.map(v=>[dot(v,right),dot(v,up),dot(v,camera)]);
      const low=[Infinity,Infinity,Infinity],high=[-Infinity,-Infinity,-Infinity];
      for(const v of projected)for(let axis=0;axis<3;axis++){low[axis]=Math.min(low[axis],v[axis]);high[axis]=Math.max(high[axis],v[axis]);}
      const mid=low.map((v,i)=>(v+high[i])/2);
      // One-pixel safety border keeps antialiased outer edges inside the PNG.
      const scale=Math.min((data.width-4)/(high[0]-low[0]),(data.height-4)/(high[1]-low[1]));
      const depthSpan=Math.max(1,high[2]-low[2]);
      const packed=[];
      for(let index=0;index<data.triangles.length;index++){
        const triangle=data.triangles[index],a=data.vertices[triangle[0]],b=data.vertices[triangle[1]],c=data.vertices[triangle[2]];
        const u=b.map((v,i)=>v-a[i]),v=c.map((x,i)=>x-a[i]);
        const normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
        const norm=Math.hypot(...normal);if(!(norm>0))throw Error('Collapsed model triangle');
        const n=normal.map(value=>value/norm),centre=data.centres?.[index];
        // A restrained cavity tint distinguishes inward-facing walls in the
        // editorial render; the actual surface positions are unchanged.
        const inward=centre&&Math.abs(n[2])<.8&&(n[0]*((a[0]+b[0]+c[0])/3-centre[0])+n[1]*((a[1]+b[1]+c[1])/3-centre[1]))<-.2;
        const colour=data.colours[index].map(value=>value/255*(inward?.76:1));
        for(const vertex of triangle){const p=projected[vertex];packed.push((p[0]-mid[0])*scale*2/data.width,(p[1]-mid[1])*scale*2/data.height,-(p[2]-mid[2])*1.8/depthSpan,...n,...colour);}
      }
      const vao=gl.createVertexArray();gl.bindVertexArray(vao);
      const buffer=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,buffer);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(packed),gl.STATIC_DRAW);
      for(let index=0;index<3;index++){gl.enableVertexAttribArray(index);gl.vertexAttribPointer(index,3,gl.FLOAT,false,36,index*12);}
      gl.viewport(0,0,data.width,data.height);gl.clearColor(0,0,0,0);gl.clearDepth(1);
      gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LESS);gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);
      gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.drawArrays(gl.TRIANGLES,0,data.triangles.length*3);gl.finish();
      if(gl.getError()!==gl.NO_ERROR)throw Error('WebGL model render failed');
      const pixels=new Uint8Array(data.width*data.height*4);gl.readPixels(0,0,data.width,data.height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
      let painted=0;for(let index=3;index<pixels.length;index+=4)if(pixels[index])painted++;
      if(painted<data.width*data.height*.05)throw Error('Unexpectedly empty model render');
      return {triangles:data.triangles.length,paintedPixels:painted};
    },scene);
    fs.mkdirSync(path.dirname(destination),{recursive:true});
    await page.screenshot({path:destination,omitBackground:true});
    console.log(JSON.stringify(report));
  }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});

	subroutine zgrid(z,nxsize,nysize,nx,ny,x1,y1,dx,dy, 
     1	xp,yp,zp,n,cay,nrng) 
*
*
*  This software was developed by the Thermal Modeling and Analysis
*  Project(TMAP) of the National Oceanographic and Atmospheric
*  Administration's (NOAA) Pacific Marine Environmental Lab(PMEL),
*  hereafter referred to as NOAA/PMEL/TMAP.
*
*  Access and use of this software shall impose the following
*  obligations and understandings on the user. The user is granted the
*  right, without any fee or cost, to use, copy, modify, alter, enhance
*  and distribute this software, and any derivative works thereof, and
*  its supporting documentation for any purpose whatsoever, provided
*  that this entire notice appears in all copies of the software,
*  derivative works and supporting documentation.  Further, the user
*  agrees to credit NOAA/PMEL/TMAP in any publications that result from
*  the use of this software or in any product that includes this
*  software. The names TMAP, NOAA and/or PMEL, however, may not be used
*  in any advertising or publicity to endorse or promote any products
*  or commercial entity unless specific written permission is obtained
*  from NOAA/PMEL/TMAP. The user also understands that NOAA/PMEL/TMAP
*  is not obligated to provide the user with any support, consulting,
*  training or assistance of any kind with regard to the use, operation
*  and performance of this software nor to provide the user with any
*  updates, revisions, new versions or "bug fixes".
*
*  THIS SOFTWARE IS PROVIDED BY NOAA/PMEL/TMAP "AS IS" AND ANY EXPRESS
*  OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
*  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
*  ARE DISCLAIMED. IN NO EVENT SHALL NOAA/PMEL/TMAP BE LIABLE FOR ANY SPECIAL,
*  INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER
*  RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF
*  CONTRACT, NEGLIGENCE OR OTHER TORTUOUS ACTION, ARISING OUT OF OR IN
*  CONNECTION WITH THE ACCESS, USE OR PERFORMANCE OF THIS SOFTWARE. 
*
*
C**    @(#)zgrid.f	1.1    3/10/88
C**
C**
C***********************************************************************
C**
C**                 PLOT+ Scientific Graphics System
C**
C***********************************************************************
C**
C**
c     sets up square grid for contouring , given arbitrarily placed 
c     data points. laplace interpolation is used. 
c     the method used here was lifted directly from notes left by 
c     mr ian crain formerly with the comp.science div. 
c     info on relaxation soln of laplace eqn supplied by dr t murty. 
c     fortran ii   oceanography/emr   dec/68   jdt 
c 
c     z = 2-d array of hgts to be set up. points outside region to be 
c     contoured should be initialized to 10**35 . the rest should be 0.0 
c     nx,ny = max subscripts of z in x and y directions . 
c     x1,y1 = coordinates of z(1,1) 
c     dx,dy = x and y increments . 
c     xp,yp,zp = arrays giving position and hgt of each data point. 
c     n = size of arrays xp,yp and zp . 
c 
c     modification feb/69   to get smoother results a portion of the 
c     beam eqn  was added to the laplace eqn giving 
c     delta2x(z)+delta2y(z) - k(delta4x(z)+delta4y(z)) = 0 . 
c     k=0 gives pure laplace solution.  k=inf. gives pure spline solution. 
c     cayin = k = amount of spline eqn (between 0 and inf.) 
c     nrng...grid points more than nrng grid spaces from the nearest 
c            data point are set to undefined. 
c 
c     modification dec23/69   data pts no longer moved to grid pts. 
c 
c     modification may 5 79  common blocks work1 and work2 must 
c     be dimension at least n points long by the user.  common 
c     block work3 must be dimensioned at least ny points long. 
c 
c	modification june 17,1985 - handles data values of 1e35. if at
c	least one data value near a grid point is equal to 1e35, the z
c	array is initialized to 1e35 at that grid point
c	- by g.r. halliwell
c
c*******************************************************************************
c 
c	vax/vms
c
	dimension z(nxsize,nysize),xp(n),yp(n),zp(n),
     .	zpij(50000),knxt(50000)
c
c	end vax/vms
c
c	rsx-11m
c
c	virtual z(nxsize,nysize),xp(n),yp(n),zp(n),zpij(10000),knxt(10000)
c
c	end rsx-11m
c
	dimension imnew(1000),kksav(500)
 
	itmax=100 
	eps=.002 
	big=.9e35 
c 
c     get zbase which will make all zp values positive by 20*(zmax-zmin) 
c*******************************************************************************
c 
c**   grh modification
	zmin=big
	zmax=-big
	do 20 k=1,n 
	if(zp(k).ge.1e35)goto 20
c**
	if(zp(k)-zmax)14,14,12 
12	zmax=zp(k) 
14	if(zp(k)-zmin)16,20,20 
16	zmin=zp(k) 
20	continue 
	zrange=zmax-zmin 
	zbase=zrange*20.-zmin 
	hrange=amin1(dx*(nx-1) , dy*(ny-1)) 
	derzm=2.*zrange/hrange 
c 
c     set pointer array knxt 
c*******************************************************************************
c 
	do 60 kk=1,n 
	k=1+n-kk 
	knxt(k)=0 
	i= (xp(k)-x1)/dx + 1.5 
	if(i*(nx+1-i))60,60,35 
35	j= (yp(k)-y1)/dy + 1.5 
	if(j*(ny+1-j))60,60,40 
40	if(z(i,j)-big)45,60,60 
45	knxt(k)=n+1 
	if(z(i,j))55,55,50 
50	knxt(k)= z(i,j)+.5 
55	z(i,j)=k 
60	continue 
c 
c     affix each data point zp to its nearby grid point.  take avg zp if 
c     more than one zp nearby the grid point. add zbase and complement. 
	do 80 k=1,n 
	if(knxt(k))80,80,65 
65	npt=0 
c**   grh modification
	imask=0
c**
	zsum=0. 
	i= (xp(k)-x1)/dx + 1.5 
	j =(yp(k)-y1)/dy + 1.5 
	kk=k 
70	npt=npt+1 
c**   grh modification
	kksav(npt)=kk
	if(zp(kk).gt.big)imask=1
c**
	zsum=zsum+ zp(kk) 
	knxt(kk)=-knxt(kk) 
	kk = -knxt(kk) 
	if(kk-n)70,70,75 
c**	grh modification
75	if(imask.eq.0)then
	z(i,j) = -zsum/npt-zbase 
	else
	z(i,j) = 1.e35
	do 76 i=1,npt
76	knxt(kksav(i))=0
	endif
c**
80	continue 
c 
c     initially set each unset grid point to value of nearest known pt. 
c*******************************************************************************
c 
	do 110 i=1,nx 
	do 110 j=1,ny 
	if(z(i,j))110,100,110 
100	z(i,j) = -1.e35 
110	continue 
	do 199 iter=1,nrng 
	nnew=0 
	do 197 i=1,nx 
	do 197 j=1,ny 
	if(z(i,j)+big)152,192,192 
152	if(j-1)162,162,153 
153	if(jmnew)154,154,162 
154	zijn=abs(z(i,j-1)) 
	if(zijn-big)195,162,162 
162	if(i-1)172,172,163 
163	if(imnew(j))164,164,172 
164	zijn=abs(z(i-1,j)) 
	if(zijn-big)195,172,172 
172	if(j-ny)173,182,182 
173	zijn=abs(z(i,j+1)) 
	if(zijn-big)195,182,182 
182	if(i-nx)183,192,192 
183	zijn=abs(z(i+1,j)) 
	if(zijn-big)195,192,192 
192	imnew(j)=0 
	jmnew=0 
	go to 197 
195	imnew(j)=1 
	jmnew=1 
	z(i,j)=zijn 
	nnew=nnew+1 
197	continue 
	if(nnew)200,200,199 
199	continue 
200	continue 
	do 202 i=1,nx 
	do 202 j=1,ny 
	abz=abs(z(i,j)) 
	if(abz-big)202,201,201 
201	z(i,j)=abz 
202	continue 
c 
c     improve the non-data points by applying point over-relaxation 
c     using the laplace-spline equation  (carres method is used) 
c*******************************************************************************
c 
	dzrmsp=zrange 
	relax=1.0 
	do 4000 iter=1,itmax 
	dzrms=0. 
	dzmax=0. 
	npg =0 
	do 2000 i=1,nx 
	do 2000 j=1,ny 
	z00=z(i,j) 
	if(z00-big)205,2000,2000 
205	if(z00)2000,208,208 
208	wgt=0. 
	zsum=0. 
c 
	im=0 
	if(i-1)570,570,510 
510	zim=abs(z(i-1,j)) 
	if(zim-big)530,570,570 
530	im=1 
	wgt=wgt+1. 
	zsum=zsum+zim 
	if(i-2)570,570,540 
540	zimm=abs(z(i-2,j)) 
	if(zimm-big)560,570,570 
560	wgt=wgt+cay 
	zsum=zsum-cay*(zimm-2.*zim) 
570	if(nx-i)700,700,580 
580	zip=abs(z(i+1,j)) 
	if(zip-big)600,700,700 
600	wgt=wgt+1. 
	zsum=zsum+zip 
	if(im)620,620,610 
610	wgt=wgt+4.*cay 
	zsum=zsum+2.*cay*(zim+zip) 
620	if(nx-1-i)700,700,630 
630	zipp=abs(z(i+2,j)) 
	if(zipp-big)650,700,700 
650	wgt=wgt+cay 
	zsum=zsum-cay*(zipp-2.*zip) 
700	continue 
c 
	jm=0 
	if(j-1)1570,1570,1510 
1510	zjm=abs(z(i,j-1)) 
	if(zjm-big)1530,1570,1570 
1530	jm=1 
	wgt=wgt+1. 
	zsum=zsum+zjm 
	if(j-2)1570,1570,1540 
1540	zjmm=abs(z(i,j-2)) 
	if(zjmm-big)1560,1570,1570 
1560	wgt=wgt+cay 
	zsum=zsum-cay*(zjmm-2.*zjm) 
1570	if(ny-j)1700,1700,1580 
1580	zjp=abs(z(i,j+1)) 
	if(zjp-big)1600,1700,1700 
1600	wgt=wgt+1. 
	zsum=zsum+zjp 
	if(jm)1620,1620,1610 
1610	wgt=wgt+4.*cay 
	zsum=zsum+2.*cay*(zjm+zjp) 
1620	if(ny-1-j)1700,1700,1630 
1630	zjpp=abs(z(i,j+2)) 
	if(zjpp-big)1650,1700,1700 
1650	wgt=wgt+cay 
	zsum=zsum-cay*(zjpp-2.*zjp) 
1700	continue 
c 
	dz=zsum/wgt-z00 
	npg=npg+1 
	dzrms=dzrms+dz*dz 
	dzmax=amax1(abs(dz),dzmax) 
	z(i,j)=z00+dz*relax 
2000	continue 
c 
c 
c     shift data points zp progressively back to their proper places as 
c     the shape of surface z becomes evident. 
c*******************************************************************************
c 
	if(iter-(iter/10)*10) 3600,3020,3600 
3020	do 3400 k=1,n 
	knxt(k) =iabs(knxt(k)) 
	if(knxt(k))3400,3400,3030 
3030	x=(xp(k)-x1)/dx 
	i=x+1.5 
	x= x+1.-i 
	y=(yp(k)-y1)/dy 
	j=y+1.5 
	y=y+1.-j 
	zpxy = zp(k)+zbase 
	z00 = abs(z(i,j)) 
c 
	zw=1.e35 
	if(i-1)3120,3120,3110 
3110	zw = abs(z(i-1,j)) 
3120	ze=1.e35 
	if(i-nx)3130,3140,3140 
3130	ze = abs(z(i+1,j)) 
3140	if(ze-big)3160,3150,3150 
3150	if(zw-big)3180,3170,3170 
3160	if(zw-big)3200,3190,3190 
3170	ze=z00 
	zw=z00 
	go to 3200 
3180	ze=2.*z00-zw 
	go to 3200 
3190	zw = 2.*z00-ze 
c 
3200	zs=1.e35 
	if(j-1)3220,3220,3210 
3210	zs = abs(z(i,j-1)) 
3220  	zn= 1.e35 
	if(j-ny)3230,3240,3240 
3230	zn = abs(z(i,j+1)) 
3240	if(zn-big)3260,3250,3250 
3250	if(zs-big)3280,3270,3270 
3260	if(zs-big)3300,3290,3290 
3270	zn= z00 
	zs= z00 
	go to 3300 
3280	zn = 2.*z00-zs 
	go to 3300 
3290	zs = 2.*z00-zn 
c 
3300	a=(ze-zw)*.5 
	b=(zn-zs)*.5 
	c=(ze+zw)*.5-z00 
	d=(zn+zs)*.5-z00 
	zxy=z00+a*x+b*y+c*x*x+d*y*y 
	delz=z00-zxy 
	delzm=derzm*(abs(x)*dx+abs(y)*dy)*.80 
	if(delz-delzm)3355,3355,3350 
3350	delz=delzm 
3355	if(delz+delzm)3360,3365,3365 
3360	delz=-delzm 
3365	zpij(k)=zpxy+delz 
3400	continue 
c 
	do 3500 k=1,n 
	if(knxt(k))3500,3500,3410 
3410	npt=0 
	zsum = 0. 
	i= (xp(k)-x1)/dx + 1.5 
	j= (yp(k)-y1)/dy + 1.5 
	kk = k 
3420	npt = npt+1 
	zsum = zsum + zpij(kk) 
	knxt(kk)= -knxt(kk) 
	kk = -knxt(kk) 
	if(kk-n)3420,3420,3430 
3430	z(i,j) =  -zsum/npt 
3500	continue 
3600	continue 
c 
c     test for convergence 
c*******************************************************************************
c 
	if(npg.eq.0)goto 4010
	dzrms=sqrt(dzrms/npg) 
	root =dzrms/dzrmsp 
	dzrmsp=dzrms 
	dzmaxf=dzmax/zrange 
	if(iter-(iter/10)*10-2)3715,3710,3715 
3710	dzrms8 = dzrms 
3715	if(iter-(iter/10)*10)4000,3720,4000 
3720	root = sqrt(sqrt(sqrt(dzrms/dzrms8))) 
	if(root-.9999)3730,4000,4000 
3730	if(dzmaxf/(1.-root)-eps)4010,4010,3740 
c 
c     improve the relaxation factor. 
c*******************************************************************************
c 
3740	if((iter-20)*(iter-40)*(iter-60))4000,3750,4000 
3750	if(relax-1.-root)3760,4000,4000 
3760	tpy =(root+relax-1.)/relax 
	rootgs = tpy*tpy/root 
	relaxn= 2./(1.+sqrt(1.-rootgs)) 
	if(iter-60)3780,3785,3780 
3780	relaxn= relaxn-.25*(2.-relaxn) 
3785	relax = amax1(relax,relaxn) 
4000	continue 
4010	continue 
c 
c     remove zbase from array z and return. 
c 
	do 4500 i=1,nx 
	do 4500 j=1,ny 
	if(z(i,j)-big)4400,4500,4500 
4400	z(i,j)=abs(z(i,j))-zbase 
4500	continue 
	return 
	end 

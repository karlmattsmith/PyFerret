* scat2grid_subs:  Subroutines called by the scat2grid functions.
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

      SUBROUTINE pickout1 (atim, n, val)


*  ACM 5/2003
*  Called from the ave_scat2grid_t function.
*  Pick out nth item from atim, which is really 4-D 
*  with normal axes on three of the four axes.

      REAL atim(*)
      REAL val
      INTEGER n

      val = atim(n)

      RETURN
      END


      SUBROUTINE pickout2 (alon, alat, n, xx, yy)


*  ACM 3/2000
*  Called from the scatter*  gridding functins.
*  Pick out nth item from alon and alat, which are really 4-dimensioned arrays
*  with normal axes on three of the four axes.
*  (can be any variables, typically lon and lat)

      REAL alon(*), alat(*)
      REAL xx, yy
      INTEGER n

      xx = alon(n)
      yy = alat(n)

      RETURN
      END

      SUBROUTINE pickout3 (alon, alat, atimes, n, xx, yy, tt)

*  CALLed from the scatter*  gridding functins.
*  Pick out nth item from alon and alat, which are really 4-dimensioned arrays
*  with normal axes on three of the four axes.
*  (can be any variables, typically lon,lat,time or lon,lat,depth)

      REAL alon(*), alat(*), atimes(*)
      REAL xx, yy, tt
      INTEGER n

      xx = alon(n)
      yy = alat(n)
      tt = atimes(n)

      RETURN
      END

      SUBROUTINE pickout4 (alon, alat, atimes, vals, n, xx, yy, tt, vv)

*  Called from the scatter*  gridding functins.
*  Pick out nth item from alon and alat, which are really 4-dimensioned arrays
*  with normal axes on three of the four axes.
*  (can be any variables, typically lon,lat,time,value or lon,lat,depth,time, etc)

      REAL alon(*), alat(*), atimes(*), vals(*)
      REAL xx, yy, tt, vv
      INTEGER n

      xx = alon(n)
      yy = alat(n)
      tt = atimes(n)
      vv = vals(n)

      RETURN
      END

c************************************************************************
c...NOBS.....Based on gausswt, return only the # of obs in (x,y) gridbox
c............method is to call this sub for each data value
c............all calcs done in gridbox units
c............xx/x1/xf all in same units
c............yy/y1/yf all in same units

c  i	xx,yy=x/y location of data pt (data units)
c  i	nx,ny=size of grids
c  i	x1,y1=west/south edge of grid (center of 1st box in data units)
c  o 	obs(nx,ny) number of obs in each (x,y) gridbox
c--------------------------------------------------------------------------

	SUBROUTINE nobs (xx, yy, nx, ny, x1, y1, dx, dy, 
     .			 xf, yf, obs)


* Argument declarations

        INTEGER nx, ny
	REAL xx, yy, dx, dy, x1, y1, xf, yf, obs(nx,ny)

* Local variable declarations

        REAL xxg, yyg
        INTEGER ig, jg

	xxg = (xx-x1)/ dx + 1.		  ! grid values of data location
	yyg = (yy-y1)/ dy + 1.

c.................save the number of obs in each (x,y) gridbox
	ig = NINT(xxg)
	jg = NINT(yyg)
	IF (ig.GE.1 .AND. ig.LE.nx .AND. jg.GE.1 .AND. jg.LE.ny)
     .		obs(ig,jg) = obs(ig,jg)+1.

	RETURN
	END



c************************************************************************
c...NOBS.....Based on gausswt, return only the # of obs in (x,y) gridbox
c............method is to call this sub for each data value
c............all calcs done in gridbox units
c............xx/x1/xf all in same units
c............yy/y1/yf all in same units

c  i	xx,yy,tt=x/y/t location of data pt (data units)
c  i	nx,ny,nt=size of grids
c  i	x1,y1,L1=west/south/earliest edge of grid (center of 1st box in data units)
c  o 	obs(nx,ny,nt) number of obs in each (x,y,t) gridbox
c--------------------------------------------------------------------------

	SUBROUTINE nobsxyt (xx, yy, tt, nx, ny, nt, x1, y1, t1, 
     .                 dx, dy, dt, xf, yf, tf, obs)


* Argument declarations

        INTEGER nx, ny, nt
	REAL xx, yy, tt, x1, y1, t1, dx, dy, dt, xf, 
     .       yf, tf, obs(nx,ny,nt)

* Local variable declarations

        REAL xxg, yyg, ttg
        INTEGER ig, jg, Lg ! !!!!!!!!!!!!!!!!!!!!!!!! adding t dimension throughtout

	xxg = (xx-x1)/ dx + 1.		  ! grid values of data location
	yyg = (yy-y1)/ dy + 1.
	ttg = (tt-t1)/ dt + 1.

c.................save the number of obs in each (x,y,t) gridbox
	ig = NINT(xxg)
	jg = NINT(yyg)
	Lg = NINT(ttg)
	IF (ig.GE.1 .AND. ig.LE.nx .AND. jg.GE.1 .AND. jg.LE.ny .AND.
     .      Lg.GE.1 .AND. Lg.LE.nt   )
     .		obs(ig,jg,Lg) = obs(ig,jg,Lg)+1.

	RETURN
	END


      SUBROUTINE pickout (atim, n, val)


*  ACM 5/2003
*  Called from the ave_scat2grid_t function.
*  Pick out nth item from atim, which is really 4-D 
*  with normal axes on three of the four axes.

      REAL atim(*)
      REAL val
      INTEGER n

      val = atim(n)

      RETURN
      END

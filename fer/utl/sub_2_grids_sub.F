	SUBROUTINE SUB_2_GRIDS_SUB (
     .		plus, plox, phix, ploy, phiy, ploz, phiz, plot, phit, 
     .		ploe, phie, plof, phif, bad_plus,
     .		mnus, mlox, mhix, mloy, mhiy, mloz, mhiz, mlot, mhit, 
     .		mloe, mhie, mlof, mhif, bad_mnus,
     .		rslt, rlox, rhix, rloy, rhiy, rloz, rhiz, rlot, rhit, 
     .		rloe, rhie, rlof, rhif, bad_rslt )

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
* subtract 2 grids producing a third

* programmer - steve hankin
* NOAA/PMEL, Seattle, WA - Tropical Modeling and Analysis Program
* written for VAX computer under VMS operating system
*
* V200: 10/12/89
*       *acm* 3/12 Add E and F dimensions (use nferdims in tmap_dims.parm)

        IMPLICIT NONE
	include 'tmap_dims.parm'
	include 'ferret.parm'

* calling argument declarations:
	INTEGER	plox, phix, ploy, phiy, ploz, phiz, plot, phit, 
     .		ploe, phie, plof, phif,
     .		mlox, mhix, mloy, mhiy, mloz, mhiz, mlot, mhit, 
     .		mloe, mhie, mlof, mhif,
     .		rlox, rhix, rloy, rhiy, rloz, rhiz, rlot, rhit, 
     .		rloe, rhie, rlof, rhif
	REAL    plus( plox:phix,ploy:phiy,ploz:phiz,plot:phit,ploe:phie,plof:phif ),
     .		mnus( mlox:mhix,mloy:mhiy,mloz:mhiz,mlot:mhit,mloe:mhie,mlof:mhif ),
     .		rslt( rlox:rhix,rloy:rhiy,rloz:rhiz,rlot:rhit,rloe:rhie,rlof:rhif )
	REAL	bad_plus, bad_mnus, bad_rslt

* internal variable declarations:
	INTEGER	i, j, k, l, m, n

* --- end of introductory code ---

	DO 100 n = rlof, rhif
	DO 100 m = rloe, rhie
	DO 100 l = rlot, rhit
	DO 100 k = rloz, rhiz
	DO 100 j = rloy, rhiy
	DO 100 i = rlox, rhix

	   IF (  plus(i,j,k,l,m,n) .NE. bad_plus
     .	   .AND. mnus(i,j,k,l,m,n) .NE. bad_mnus ) THEN

	      rslt(i,j,k,l,m,n) = plus(i,j,k,l,m,n) - mnus(i,j,k,l,m,n)

	   ELSE

	      rslt(i,j,k,l,m,n) = bad_rslt

	   ENDIF

 100	CONTINUE

	RETURN
	END 

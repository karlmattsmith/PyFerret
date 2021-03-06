        SUBROUTINE WS_LINE_BUNDLES(zwsid,zwstype)

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
*  the use of this software or in any product that INCLUDEs this
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
*       Routine to set up the line bundles for generic WSs.
*       J Davison JISAO/PMEL/TMAP 3.23.89
*       *jd* 2.19.92 mod to support atc gks
*       *jd* 8.10.93 mod to support XGKS line colors -- force setting
*       *js* 7.31.97 mod to change call to gqlwk to query_xgks_wkstn

*       *acm* 8/2001  add polymarker call for PLOT/SYMBOL=DOT  
*       *acm* 4/2002  add polymarker calls for circles of different sizes
*                     and colors 1-6 are colored dots, 7-12 are small circles
*                     13-18 are larger circles.  /THICK makes them thicker.

* gsplr: wkid, line index, line type, linewidth scale factor, color index
* gspmr: wkid, marker index, marker type(dot=1), size (const for dot), color index

*        *acm* 12/4/02 NOTE: With changes to gksm2ps.c which multiply the 
*              size of the dots by 4, the output is consistent from 
*              ferret metafiles transformed to postscript, from 
*              "ferret -batch" output, and gif files.
*       *acm* 2/2003 polymarker dot line bundles had not been set for pen > 6
*  v600 *acm* 5/2006 User can change the number of line colors.
*  PyFr *kms* 5/13 Add alpha channel (opaque)
*  PyFr *kms* 7/13 Add white as color 7, grays start with 8; remove setup for monochrome

        IMPLICIT NONE
        INCLUDE 'parampl5_dat.decl'
        INCLUDE 'PARAMPL5.DAT'
        INCLUDE 'plt_inc.decl'
        INCLUDE 'PLT.INC'
        INCLUDE 'pen_inc.decl'  ! with num_line_colors
        INCLUDE 'PEN.INC'
        INCLUDE 'save_colors.cmn'

        integer zwsid, zwstype
        integer j, fktr, index
        real    thickness, grey, frac

*******************************************************************************

*       COLOR WORKSTATIONS:
*       pre-defined colors
        call FGD_GSCR(zwsid,2,1.0,0.0,0.0,1.0)
        call FGD_GSCR(zwsid,3,0.0,1.0,0.0,1.0)
        call FGD_GSCR(zwsid,4,0.0,0.0,1.0,1.0)
        call FGD_GSCR(zwsid,5,0.0,1.0,1.0,1.0)
        call FGD_GSCR(zwsid,6,1.0,0.0,1.0,1.0) 
        call FGD_GSCR(zwsid,7,1.0,1.0,1.0,1.0) 
     
! Set up initial values for further colors as grey
! range them between 0.6,0.6,0.6 and 0.9,0.9,0.9

        IF (num_line_colors .GT. 7) THEN
           frac = (0.8-0.4)/FLOAT(num_line_colors - 7)
           grey = 0.8
           DO 40 j = 8, num_line_colors
              call FGD_GSCR(zwsid,j,grey,grey,grey,1.0)
              grey = grey - frac
  40       CONTINUE
        ENDIF

        IF (saved_line_colors .GT. 0) THEN
           CALL restore_saved_line_colors (zwsid)
        ENDIF

! Set line bundles

        do 20 j = 1, num_line_colors
           do 10 fktr = 1,3     ! thickness
              index = (fktr-1)*num_line_colors+j
              thickness = fktr
              CALL FGD_GSPLR(zwsid, index, 1, thickness, j)
10         continue
20      continue

        return

        end

      SUBROUTINE MIRROR(IMIRA,IMIRB)
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
C**    @(#)mirror.f	1.1    3/10/88
C**
C**
C***********************************************************************
C**
C**                 PLOT+ Scientific Graphics System
C**
C***********************************************************************
C**
C**
C
C     CALL MIRROR(IMIRA,IMIRB)
C
C     THIS SUBROUTINE SELECTS THE TYPE OF MIRROR IMAGE, IF ANY,
C     WHICH WILL BE DRAWN.
C
C     THE VARIOUS PARAMETERS AND THEIR DEFINITIONS ARE LISTED
C     BELOW:
C        IMIRA  - HORIZONTAL MIRROR-IMAGE CODE (0 = OFF, NON-
C                 ZERO = ON).
C        IMIRB  - VERTICAL MIRROR-IMAGE CODE (0 = OFF, NON-ZERO
C                 = ON).
C
C
#ifdef unix
	include 'PLTCOM.DAT'
#else
	include 'pplinc:PLTCOM.DAT'
#endif
C
C     SET THE MIRROR-IMAGE FLAGS.
C
      MIRAF = .FALSE.
      IF(IMIRA .NE. 0)MIRAF = .TRUE.
      MIRBF = .FALSE.
      IF(IMIRB .NE. 0)MIRBF = .TRUE.
      RETURN
C
      END

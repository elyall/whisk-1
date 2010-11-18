# Locate ffmpeg
#
# Output
# ------
# FFMPEG_LIBRARIES
# FFMPEG_FOUND
# FFMPEG_INCLUDE_DIR
#
# Input
# -----
# ROOT_3RDPARTY_DIR
#    Location of 3rd party libraries for a project
#    It is searched last, so system libraries will be have priority.
# $FFMPEG_DIR       
#    an environment variable that would
#    correspond to the ./configure --prefix=$FFMPEG_DIR
#
# Created by Robert Osfield.
# Modified by Nathan Clack.


# Notes
# -----
# In ffmpeg code, old version use "#include <header.h>" and newer use "#include <libname/header.h>"
# Use "#include <header.h>" for compatibility with old version of ffmpeg
# We have to search the path which contain the header.h (usefull for old version)
# and search the path which contain the libname/header.h (usefull for new version)
# Then we need to include ${FFMPEG_libname_INCLUDE_DIRS} (in old version case, use by ffmpeg header and osg plugin code)
#                                                       (in new version case, use by ffmpeg header) 
# and ${FFMPEG_libname_INCLUDE_DIRS/libname}             (in new version case, use by osg plugin code)


# Macro to find header and lib directories
# example: FFMPEG_FIND(AVFORMAT avformat avformat.h)
MACRO(FFMPEG_FIND varname shortname headername)
    # old version of ffmpeg put header in $prefix/include/[ffmpeg]
    # so try to find header in include directory
    FIND_PATH(FFMPEG_${varname}_INCLUDE_DIRS ${headername}
        PATHS
          ${FFMPEG_ROOT}/include
          $ENV{FFMPEG_DIR}/include
          $ENV{OSGDIR}/include
          $ENV{OSG_ROOT}/include
          ~/Library/Frameworks
          /Library/Frameworks
          /usr/local/include
          /usr/include
          /sw/include # Fink
          /opt/local/include # DarwinPorts
          /opt/csw/include # Blastwave
          /opt/include
          /usr/freeware/include
          ${ROOT_3RDPARTY_DIR}
        PATH_SUFFIXES 
          ffmpeg
          ffmpeg/w32/msvc/include
          ffmpeg/w32/ming/include
        DOC "Location of FFMPEG Headers"
    )

    # newer version of ffmpeg put header in $prefix/include/[ffmpeg/]lib${shortname}
    # so try to find lib${shortname}/header in include directory
    IF(NOT FFMPEG_${varname}_INCLUDE_DIRS)
        FIND_PATH(FFMPEG_${varname}_INCLUDE_DIRS lib${shortname}/${headername}
              ${FFMPEG_ROOT}/include
              $ENV{FFMPEG_DIR}/include
              $ENV{OSGDIR}/include
              $ENV{OSG_ROOT}/include
              ~/Library/Frameworks
              /Library/Frameworks
              /usr/local/include
              /usr/include/
              /sw/include # Fink
              /opt/local/include # DarwinPorts
              /opt/csw/include # Blastwave
              /opt/include
              /usr/freeware/include
              ${ROOT_3RDPARTY_DIR}
            PATH_SUFFIXES 
              ffmpeg
              ffmpeg/w32/msvc/include
              ffmpeg/w32/ming/include
            DOC "Location of FFMPEG Headers"
        )
    ENDIF(NOT FFMPEG_${varname}_INCLUDE_DIRS)

    FIND_LIBRARY(FFMPEG_${varname}_LIBRARIES
        NAMES ${shortname}
        PATHS
          ${FFMPEG_ROOT}
          $ENV{FFMPEG_DIR}
          ~/Library/Frameworks
          /Library/Frameworks
          /usr/local
          /usr
          /sw
          /opt/local
          /opt/csw
          /opt
          /usr/freeware
          ${ROOT_3RDPARTY_DIR}
        PATH_SUFFIXES 
          lib
          lib64
          w32/msvc/lib
          w32/ming/lib
        DOC "Location of FFMPEG Libraries"
    )

    IF (FFMPEG_${varname}_LIBRARIES AND FFMPEG_${varname}_INCLUDE_DIRS)
        SET(FFMPEG_${varname}_FOUND 1)
    ENDIF(FFMPEG_${varname}_LIBRARIES AND FFMPEG_${varname}_INCLUDE_DIRS)

ENDMACRO(FFMPEG_FIND)

SET(FFMPEG_ROOT "$ENV{FFMPEG_DIR}" CACHE PATH "Location of FFMPEG")

FFMPEG_FIND(LIBAVFORMAT avformat avformat.h)
FFMPEG_FIND(LIBAVDEVICE avdevice avdevice.h)
FFMPEG_FIND(LIBAVCODEC  avcodec  avcodec.h)
FFMPEG_FIND(LIBAVUTIL   avutil   avutil.h)
FFMPEG_FIND(LIBSWSCALE  swscale  swscale.h)

SET(FFMPEG_FOUND "NO")
# Note we don't check FFMPEG_LIBSWSCALE_FOUND here; it's optional.
IF   (FFMPEG_LIBAVFORMAT_FOUND AND FFMPEG_LIBAVDEVICE_FOUND AND FFMPEG_LIBAVCODEC_FOUND AND FFMPEG_LIBAVUTIL_FOUND AND FFMPEG_LIBSWSCALE_FOUND)

    SET(FFMPEG_FOUND "YES")

    SET(FFMPEG_INCLUDE_DIRS ${FFMPEG_LIBAVFORMAT_INCLUDE_DIRS})

    SET(FFMPEG_LIBRARY_DIRS ${FFMPEG_LIBAVFORMAT_LIBRARY_DIRS})

    # Note we don't add FFMPEG_LIBSWSCALE_LIBRARIES here; it will be added if found later.
    SET(FFMPEG_LIBRARIES
        ${FFMPEG_LIBAVFORMAT_LIBRARIES}
        ${FFMPEG_LIBAVDEVICE_LIBRARIES}
        ${FFMPEG_LIBAVCODEC_LIBRARIES}
        ${FFMPEG_LIBAVUTIL_LIBRARIES}
        ${FFMPEG_LIBSWSCALE_LIBRARIES}
        )

ELSE ()

#    MESSAGE(STATUS "Could not find FFMPEG")

ENDIF()
# Copyright 2025 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

import os

from tools.utils import exit_with_error

TAG = 'release-3.2.2'
HASH = 'efcb8dfdbf31583eef2fff8871286fae0600d1976ae14d7e2b6d767e6fa0b33fa8b4ada9490ee15598e7778aaf1f995c8408124cbaa930b5b51a4d3e44cadb14'

deps = ['sdl3']
variants = {
  'sdl3_mixer-mp3': {'SDL3_MIXER_FORMATS': ['mp3']},
  'sdl3_mixer-none': {'SDL3_MIXER_FORMATS': []},
  'sdl3_mixer-mp3-mt': {'SDL3_MIXER_FORMATS': ['mp3'], 'PTHREADS': 1},
  'sdl3_mixer-none-mt': {'SDL3_MIXER_FORMATS': [], 'PTHREADS': 1},
}

OPTIONS = {
  'formats': 'A comma separated list of formats (ex: --use-port=sdl3_mixer:formats=ogg,mp3)',
}

SUPPORTED_FORMATS = {'ogg', 'mp3', 'mid'}

# user options (from --use-port)
opts: dict[str, set] = {
  'formats': set(),
}


def needed(settings):
  return settings.USE_SDL_MIXER == 3


def get_formats(settings):
  formats = opts['formats'].union(settings.SDL3_MIXER_FORMATS)
  unsupported = formats - SUPPORTED_FORMATS
  if unsupported:
    exit_with_error(f'unsupported SDL3_MIXER_FORMATS: {", ".join(sorted(unsupported))}')
  return formats


def get_lib_name(settings):
  formats = '-'.join(sorted(get_formats(settings)))

  libname = 'libSDL3_mixer'
  if formats:
    libname += '-' + formats
  if settings.PTHREADS:
    libname += '-mt'
  libname += '.a'

  return libname


def get(ports, settings, shared):
  ports.fetch_project('sdl3_mixer', f'https://github.com/libsdl-org/SDL_mixer/archive/{TAG}.zip', sha512hash=HASH)
  libname = get_lib_name(settings)

  def create(final):
    source_path = ports.get_dir('sdl3_mixer', 'SDL_mixer-' + TAG)
    formats = get_formats(settings)
    source_dir = os.path.join(source_path, 'src')

    flags = [
      '-sUSE_SDL=3',
      '-DBUILD_SDL',
      '-DSDL_BUILD_MAJOR_VERSION=3',
      '-DSDL_BUILD_MINOR_VERSION=2',
      '-DSDL_BUILD_MICRO_VERSION=2',
      '-DDECODER_AIFF',
      '-DDECODER_AU',
      '-DDECODER_VOC',
      '-DDECODER_WAV',
    ]
    srcs = [
      'src/SDL_mixer.c',
      'src/SDL_mixer_metadata_tags.c',
      'src/SDL_mixer_spatialization.c',
      'src/decoder_aiff.c',
      'src/decoder_au.c',
      'src/decoder_raw.c',
      'src/decoder_sinewave.c',
      'src/decoder_voc.c',
      'src/decoder_wav.c',
    ]

    if 'ogg' in formats:
      flags.append('-DDECODER_OGGVORBIS_STB')
      srcs.append('src/decoder_stb_vorbis.c')

    if 'mp3' in formats:
      flags.append('-DDECODER_MP3_DRMP3')
      srcs.append('src/decoder_drmp3.c')

    if 'mid' in formats:
      flags.append('-DDECODER_MIDI_TIMIDITY')
      srcs += [
        'src/decoder_timidity.c',
        'src/timidity/common.c',
        'src/timidity/instrum.c',
        'src/timidity/mix.c',
        'src/timidity/output.c',
        'src/timidity/playmidi.c',
        'src/timidity/readmidi.c',
        'src/timidity/resample.c',
        'src/timidity/tables.c',
        'src/timidity/timidity.c',
      ]

    if settings.PTHREADS:
      flags.append('-pthread')

    includes = [
      os.path.join(source_path, 'include'),
      source_dir,
      os.path.join(source_dir, 'codecs'),
    ]
    ports.build_port(source_path, final, 'sdl3_mixer', flags=flags, srcs=srcs, includes=includes)
    ports.install_header_dir(os.path.join(source_path, 'include'), target='.')

  return [shared.cache.get_lib(libname, create, what='port')]


def clear(ports, settings, shared):
  shared.cache.erase_lib(get_lib_name(settings))


def process_dependencies(settings):
  settings.USE_SDL = 3


def handle_options(options, error_handler):
  formats = options['formats'].split(',')
  for format in formats:
    format = format.lower().strip()
    if not format:
      continue
    if format not in SUPPORTED_FORMATS:
      error_handler(f'{format} is not a supported format')
    else:
      opts['formats'].add(format)


def show():
  return 'sdl3_mixer (-sUSE_SDL_MIXER=3 or --use-port=sdl3_mixer; zlib license)'

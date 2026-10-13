/* Encode the renderer's stereo PCM WAV using the installed libvorbis.
 * Usage: encode_vorbis input.wav output.ogg [loop_start_samples loop_end_samples]
 * This tool is build-time only; the Godot game reads standard Ogg Vorbis files.
 */
#include <ogg/ogg.h>
#include <vorbis/vorbisenc.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void write_page(FILE *out, ogg_page *page) {
    fwrite(page->header, 1, page->header_len, out);
    fwrite(page->body, 1, page->body_len, out);
}
int main(int argc, char **argv) {
    if (argc < 3) return 2;
    FILE *in = fopen(argv[1], "rb"), *out = fopen(argv[2], "wb");
    if (!in || !out) return 3;
    unsigned char header[44];
    if (fread(header, 1, 44, in) != 44 || memcmp(header, "RIFF", 4) ||
        memcmp(header+8, "WAVEfmt ", 8) || memcmp(header+36, "data", 4)) return 4;
    vorbis_info vi; vorbis_comment vc; vorbis_dsp_state vd; vorbis_block vb;
    ogg_stream_state os; ogg_page page; ogg_packet packet, h1, h2, h3;
    vorbis_info_init(&vi);
    if (vorbis_encode_init_vbr(&vi, 2, 44100, .6f)) return 5;
    vorbis_comment_init(&vc);
    vorbis_comment_add_tag(&vc, "ENCODER", "libvorbis; original FE2 sound driver via Game Music Emu");
    if (argc >= 5) {
        vorbis_comment_add_tag(&vc, "LOOPSTART", argv[3]);
        vorbis_comment_add_tag(&vc, "LOOPEND", argv[4]);
    }
    vorbis_analysis_init(&vd, &vi); vorbis_block_init(&vd, &vb);
    ogg_stream_init(&os, 12345);
    vorbis_analysis_headerout(&vd, &vc, &h1, &h2, &h3);
    ogg_stream_packetin(&os, &h1); ogg_stream_packetin(&os, &h2); ogg_stream_packetin(&os, &h3);
    while (ogg_stream_flush(&os, &page)) write_page(out, &page);
    unsigned char bytes[4096*4];
    int eos = 0;
    while (!eos) {
        size_t n = fread(bytes, 4, 4096, in);
        float **buf = vorbis_analysis_buffer(&vd, 4096);
        for (size_t i=0; i<n; i++) {
            int16_t l = (int16_t)(bytes[4*i] | bytes[4*i+1]<<8);
            int16_t r = (int16_t)(bytes[4*i+2] | bytes[4*i+3]<<8);
            buf[0][i] = l/32768.f; buf[1][i] = r/32768.f;
        }
        vorbis_analysis_wrote(&vd, (int)n);
        while (vorbis_analysis_blockout(&vd, &vb) == 1) {
            vorbis_analysis(&vb, NULL); vorbis_bitrate_addblock(&vb);
            while (vorbis_bitrate_flushpacket(&vd, &packet)) {
                ogg_stream_packetin(&os, &packet);
                while (ogg_stream_pageout(&os, &page)) {
                    write_page(out, &page);
                    if (ogg_page_eos(&page)) eos = 1;
                }
            }
        }
    }
    ogg_stream_clear(&os); vorbis_block_clear(&vb); vorbis_dsp_clear(&vd);
    vorbis_comment_clear(&vc); vorbis_info_clear(&vi); fclose(in); fclose(out);
    return 0;
}

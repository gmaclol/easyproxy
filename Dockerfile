FROM ghcr.io/realbestia1/easyproxy:latest

ENV PORT=7860
ENV ENABLE_WARP=false
ENV FLARESOLVERR_URL=http://127.0.0.1:8191
EXPOSE 7860

COPY vixsrc.py /app/extractors/vixsrc.py

CMD python3 -m flask --app flaresolverr/app run --host=0.0.0.0 --port=8191 >/tmp/flaresolverr.log 2>&1 & sleep 5 && /bin/bash /app/entrypoint.sh

FROM ghcr.io/realbestia1/easyproxy:latest

ENV PORT=7860
ENV ENABLE_WARP=false
EXPOSE 7860

RUN python3 -c "from config_store import set; set('extractor_proxies', {'vixsrc': {'file': 'https://proxies.realbestia.com/proxies.txt'}}); print('Config populated')"

CMD /bin/bash /app/entrypoint.sh

FROM ghcr.io/realbestia1/easyproxy:latest

ENV PORT=7860
ENV API_PASSWORD=ep
ENV ENABLE_WARP=false
EXPOSE 7860

CMD ["/bin/bash", "/app/entrypoint.sh"]

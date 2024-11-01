FROM ubi9
WORKDIR /

# Copy in the source code
COPY src ./src
EXPOSE 9080

CMD ["python3", "/src/main.py"]

FROM ubuntu:20.04

# Устанавливаем переменные окружения
ENV DEBIAN_FRONTEND=noninteractive
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin

# Устанавливаем зависимости
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    zip \
    unzip \
    openjdk-8-jdk \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    build-essential \
    libsqlite3-dev \
    libreadline6-dev \
    libgdbm-dev \
    libbz2-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Python зависимости
RUN pip3 install buildozer cython==0.29.19

# Скачиваем и устанавливаем Android SDK
RUN wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip && \
    unzip commandlinetools-linux-9477386_latest.zip && \
    mkdir -p $ANDROID_HOME/cmdline-tools && \
    mv cmdline-tools $ANDROID_HOME/cmdline-tools/latest && \
    rm commandlinetools-linux-9477386_latest.zip

# Принимаем лицензии и устанавливаем компоненты SDK
RUN yes | $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager --licenses && \
    $ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-33" "build-tools;33.0.0"

# Копируем код приложения
COPY . /app
WORKDIR /app

# Собираем APK
CMD ["buildozer", "android", "debug"]

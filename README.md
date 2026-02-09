# Android BMI Calculator

## Overview

A simple Android app that calculates Body Mass Index (BMI) from user‑entered weight (kg) and height (cm), then shows a category result: Thinness, Normal, or Overweight.

## Features

- Inputs for weight (kg) and height (cm)
- BMI calculation on button press
- Category output based on BMI range

## Project Structure

```
AndroidBmi/
├── app/
│   ├── src/main/java/com/example/androidproject/MainActivity.java
│   ├── src/main/res/layout/activity_main.xml
│   └── ...
├── build.gradle
├── settings.gradle
└── gradle.properties
```

## Requirements

- Android Studio (recommended)
- Android SDK
- Gradle (via wrapper)

## How to Run

1. Open the project in Android Studio.
2. Let Gradle sync finish.
3. Run the app on an emulator or a physical device.

## Usage

1. Enter your weight in kilograms.
2. Enter your height in centimeters.
3. Tap **Calculate BMI**.
4. The BMI category and value will appear below the button.

## BMI Logic

The app uses:

```
BMI = weight_kg / (height_m * height_m)
height_m = height_cm * 0.01
```

Categories used:

- **Thinness**: BMI < 18.5
- **Normal**: 18.5 < BMI < 25
- **Overweight**: BMI > 25

## Notes

- Inputs are parsed as integers; non-numeric input will crash the app.
- BMI is currently truncated to an integer for display.
- The ranges do not include exact boundary values (e.g., 18.5, 25).

## License

Add a license if you intend to share this publicly.

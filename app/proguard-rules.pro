# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.

# Keep Retrofit
-keepattributes Signature
-keepattributes Exceptions

# Gson
-keepattributes *Annotation*
-keep class com.jeremy.bloomberg.model.** { *; }
-keep class com.jeremy.bloomberg.network.** { *; }

package com.example.yjf.automation.module;

import java.util.HashMap;
import java.util.Map;

public class ServiceManager {
    private static final Map<Class, Object> sServiceMap = new HashMap<>();

    public static <T> void register(Class<T> tClass, T object) {
        sServiceMap.put(tClass, object);
    }

    public static <T> T getService(Class<T> tClass) {
        return (T) sServiceMap.get(tClass);
    }
}

package com.example.yjf.automation.module.api;

import java.util.Map;

import io.reactivex.Single;

public interface ApiService {
    Single<ApiResponse> doPost(String path, Entity requestBody);

    Single<ApiResponse> doGet(String path, Map<String, String> query);
}

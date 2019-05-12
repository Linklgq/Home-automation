package com.example.yjf.automation.api;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import okhttp3.Interceptor;
import okhttp3.Request;
import okhttp3.Response;

public class HttpCommonInterceptor implements Interceptor {


    private Map<String, String> mHeaderParamsMap = new HashMap<>();

    public HttpCommonInterceptor() {
    }

    @Override
    public Response intercept(Chain chain) throws IOException {

//        Log.d("HttpCommonInterceptor", "add common params");
        Request oldRequest = chain.request();

        // 新的请求
        Request.Builder requestBuilder = oldRequest.newBuilder();
        requestBuilder.method(oldRequest.method(),
                oldRequest.body());

        //添加公共参数,添加到header中
        if (mHeaderParamsMap.size() > 0) {
            for (Map.Entry<String, String> params : mHeaderParamsMap.entrySet()) {
                requestBuilder.header(params.getKey(), params.getValue());
            }
        }

        requestBuilder.header("Content-Type", "application/json;charset=utf-8");
        Request newRequest = requestBuilder.build();
        return chain.proceed(newRequest);
    }
}

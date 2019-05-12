package com.example.yjf.automation.api;

import android.content.Context;
import android.util.Log;

import com.example.yjf.automation.module.api.ApiResponse;
import com.example.yjf.automation.module.api.ApiService;
import com.example.yjf.automation.module.api.Entity;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import io.reactivex.Single;
import io.reactivex.SingleEmitter;
import io.reactivex.SingleOnSubscribe;
import io.reactivex.schedulers.Schedulers;
import okhttp3.OkHttpClient;
import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.Response;
import retrofit2.Retrofit;
import retrofit2.adapter.rxjava2.RxJava2CallAdapterFactory;
import retrofit2.converter.gson.GsonConverterFactory;

import static android.support.constraint.Constraints.TAG;

public class ApiServiceImpl implements ApiService {
    private Gson gson;

    private Retrofit retrofit;

    public ApiServiceImpl(Context context) {
        // 创建 OKHttpClient
        OkHttpClient.Builder builder = new OkHttpClient.Builder();
        builder.connectTimeout(ApiConfig.DEFAULT_TIME_OUT, TimeUnit.SECONDS)
                .readTimeout(ApiConfig.DEFAULT_READ_TIME_OUT, TimeUnit.SECONDS);
        // builder.writeTimeout(DEFAULT_READ_TIME_OUT,TimeUnit.SECONDS);//写操作 超时时间
        // 添加公共参数拦截器
        HttpCommonInterceptor commonInterceptor = new HttpCommonInterceptor();
        builder.addInterceptor(commonInterceptor);

        // 创建Retrofit
        retrofit = new Retrofit.Builder()
                .client(builder.build())
                .addCallAdapterFactory(RxJava2CallAdapterFactory.create())
                .addConverterFactory(GsonConverterFactory.create())
                .baseUrl(ApiConfig.BASE_URL)
                .build();

        gson = new Gson();
    }

    @Override
    public Single<ApiResponse> doPost(String path, Entity requestBody) {
        return Single.create((SingleOnSubscribe<ApiResponse>) emitter -> {
            RetrofitApi retrofitApi = retrofit.create(RetrofitApi.class);
            Call<ResponseBody> call = retrofitApi.doPost(path, requestBody);
            doRetrofitCall(call, emitter, requestBody);
        }).subscribeOn(Schedulers.io()).unsubscribeOn(Schedulers.io());
    }

    @Override
    public Single<ApiResponse> doGet(String path, Map<String, String> query) {
        return Single.create((SingleOnSubscribe<ApiResponse>) emitter -> {
            RetrofitApi retrofitApi = retrofit.create(RetrofitApi.class);
            Call<ResponseBody> call = retrofitApi.doGet(path, query);
            doRetrofitCall(call, emitter, query);
        }).subscribeOn(Schedulers.io()).unsubscribeOn(Schedulers.io());
    }

    private void doRetrofitCall(Call<ResponseBody> call, SingleEmitter<ApiResponse> emitter, Object request)
            throws IOException {
        ApiResponse apiResponse = new ApiResponse();
        Response<ResponseBody> response = call.execute();
//        apiResponse.statusCode = response.code();
        String content;
        if (response.code() == 200) {
            content = response.body().string();
            Log.d(TAG, "doRetrofitCall: [api] response content: " + content);
            JsonObject jsonObject = gson.fromJson(content, JsonObject.class);
            apiResponse.ret = jsonObject.get("ret").getAsInt();
            apiResponse.msg = jsonObject.get("msg").toString();
        } else {
            content = "response code: " + response.code();
            apiResponse.msg = "response code: " + response.code();
        }
        Log.d(TAG, "doRetrofitCall: [api] request: " + gson.toJson(request));
        Log.d(TAG, "doRetrofitCall: [api] response: " + content);
        emitter.onSuccess(apiResponse);
    }
}

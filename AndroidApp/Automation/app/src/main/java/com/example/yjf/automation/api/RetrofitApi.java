package com.example.yjf.automation.api;

import java.util.Map;

import okhttp3.ResponseBody;
import retrofit2.Call;
import retrofit2.http.Body;
import retrofit2.http.GET;
import retrofit2.http.POST;
import retrofit2.http.QueryMap;
import retrofit2.http.Url;

public interface RetrofitApi {
    @POST
    Call<ResponseBody> doPost(@Url String path, @Body Object body);

    @GET
    Call<ResponseBody> doGet(@Url String path, @QueryMap Map<String, String> query);
}

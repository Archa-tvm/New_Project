FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY ["FlowPulse.Engine/FlowPulse.Engine.csproj", "FlowPulse.Engine/"]
RUN dotnet restore "FlowPulse.Engine/FlowPulse.Engine.csproj"

COPY . .
WORKDIR "/src/FlowPulse.Engine"
RUN dotnet build "FlowPulse.Engine.csproj" -c Release -o /app/build
RUN dotnet publish "FlowPulse.Engine.csproj" -c Release -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS final
WORKDIR /app
COPY --from=build /app/publish .

ENV ASPNETCORE_URLS=http://+:5050
EXPOSE 5050

ENTRYPOINT ["dotnet", "FlowPulse.Engine.dll"]

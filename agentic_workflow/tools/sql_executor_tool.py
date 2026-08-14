"""
SQL Executor Tool for PostgreSQL database operations.
Provides structured access to ARGO float data in PostgreSQL.
"""

import logging
import pandas as pd
from sqlalchemy import create_engine, text, bindparam
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from ..core.config import DATABASE_CONFIG, SYSTEM_CONFIG

logger = logging.getLogger(__name__)

class SQLExecutorTool:
    """Tool for executing SQL queries against the ARGO PostgreSQL database."""

    MAX_PROFILE_IDS = 100
    MAX_RESULT_ROWS = 5000

    def __init__(self, engine=None):
        self.engine = engine

    def _get_engine(self):
        """Create a bounded read-only engine on first database use."""
        if self.engine is None:
            self.engine = create_engine(
                DATABASE_CONFIG.connection_string,
                connect_args=DATABASE_CONFIG.connect_args,
                pool_pre_ping=True,
            )
        return self.engine

    def get_profile_metadata(self, profile_ids: List[str]) -> pd.DataFrame:
        """
        Get metadata for specific profiles.

        Args:
            profile_ids: List of profile IDs in format "wmo_id_cycle_number"

        Returns:
            DataFrame with profile metadata
        """
        try:
            # Parse profile IDs to extract WMO IDs and cycle numbers, binding
            # each value as a named parameter rather than interpolating it.
            conditions = []
            params: Dict[str, Any] = {}
            for i, profile_id in enumerate(profile_ids[: self.MAX_PROFILE_IDS]):
                parts = profile_id.split('_')
                if len(parts) >= 2:
                    params[f"wmo_id_{i}"] = int(parts[0])
                    params[f"cycle_{i}"] = int(parts[1])
                    conditions.append(f"(f.wmo_id = :wmo_id_{i} AND p.cycle_number = :cycle_{i})")

            if not conditions:
                return pd.DataFrame()

            where_clause = " OR ".join(conditions)

            query = text(f"""
                SELECT
                    f.wmo_id,
                    p.cycle_number,
                    p.profile_date,
                    ST_X(p.location::geometry) as longitude,
                    ST_Y(p.location::geometry) as latitude,
                    p.id as profile_db_id
                FROM profiles p
                JOIN floats f ON p.float_id = f.id
                WHERE {where_clause}
                ORDER BY f.wmo_id, p.cycle_number
                LIMIT {self.MAX_PROFILE_IDS}
            """)

            df = pd.read_sql(query, self._get_engine(), params=params)
            logger.info(f"Retrieved metadata for {len(df)} profiles")
            return df

        except Exception as e:
            logger.error(f"Failed to get profile metadata: {e}")
            return pd.DataFrame()

    def get_measurements_by_profiles(self, profile_ids: List[str]) -> pd.DataFrame:
        """
        Get all measurements for specific profiles.

        Args:
            profile_ids: List of profile IDs in format "wmo_id_cycle_number"

        Returns:
            DataFrame with measurements data
        """
        try:
            # Get profile metadata first to get database IDs
            metadata_df = self.get_profile_metadata(profile_ids)

            if metadata_df.empty:
                return pd.DataFrame()

            profile_db_ids = metadata_df['profile_db_id'].tolist()

            query = text("""
                SELECT
                    f.wmo_id,
                    p.cycle_number,
                    m.pressure,
                    m.temp,
                    m.psal,
                    ST_X(p.location::geometry) as longitude,
                    ST_Y(p.location::geometry) as latitude,
                    p.profile_date
                FROM measurements m
                JOIN profiles p ON m.profile_id = p.id
                JOIN floats f ON p.float_id = f.id
                WHERE p.id IN :profile_ids
                ORDER BY f.wmo_id, p.cycle_number, m.pressure
                LIMIT :result_limit
            """).bindparams(bindparam("profile_ids", expanding=True))

            df = pd.read_sql(
                query,
                self._get_engine(),
                params={
                    "profile_ids": profile_db_ids[: self.MAX_PROFILE_IDS],
                    "result_limit": self.MAX_RESULT_ROWS,
                },
            )
            logger.info(f"Retrieved {len(df)} measurements from {len(profile_db_ids)} profiles")
            return df

        except Exception as e:
            logger.error(f"Failed to get measurements: {e}")
            return pd.DataFrame()

    def get_profiles_by_region_and_time(self,
                                       lat_min: float, lat_max: float,
                                       lon_min: float, lon_max: float,
                                       start_date: Optional[str] = None,
                                       end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Get profiles within geographic and temporal bounds.

        Args:
            lat_min, lat_max: Latitude bounds
            lon_min, lon_max: Longitude bounds
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            DataFrame with profile metadata
        """
        try:
            conditions = [
                "ST_Y(p.location::geometry) BETWEEN :lat_min AND :lat_max",
                "ST_X(p.location::geometry) BETWEEN :lon_min AND :lon_max"
            ]
            params: Dict[str, Any] = {
                "lat_min": lat_min, "lat_max": lat_max,
                "lon_min": lon_min, "lon_max": lon_max
            }

            if start_date:
                conditions.append("p.profile_date >= :start_date")
                params["start_date"] = start_date
            if end_date:
                conditions.append("p.profile_date <= :end_date")
                params["end_date"] = end_date

            where_clause = " AND ".join(conditions)

            query = text(f"""
                SELECT
                    f.wmo_id,
                    p.cycle_number,
                    p.profile_date,
                    ST_X(p.location::geometry) as longitude,
                    ST_Y(p.location::geometry) as latitude,
                    p.id as profile_db_id
                FROM profiles p
                JOIN floats f ON p.float_id = f.id
                WHERE {where_clause}
                ORDER BY p.profile_date, f.wmo_id, p.cycle_number
                LIMIT :result_limit
            """)
            params["result_limit"] = self.MAX_RESULT_ROWS

            df = pd.read_sql(query, self._get_engine(), params=params)
            logger.info(f"Found {len(df)} profiles in specified region and time range")
            return df

        except Exception as e:
            logger.error(f"Failed to get profiles by region and time: {e}")
            return pd.DataFrame()

    def get_temperature_salinity_profiles(self, profile_ids: List[str]) -> pd.DataFrame:
        """
        Get temperature and salinity profiles with depth for specific profiles.

        Args:
            profile_ids: List of profile IDs

        Returns:
            DataFrame with T-S profile data
        """
        measurements_df = self.get_measurements_by_profiles(profile_ids)

        if measurements_df.empty:
            return pd.DataFrame()

        # Filter out invalid measurements
        valid_df = measurements_df.dropna(subset=['temp', 'psal', 'pressure'])
        valid_df = valid_df[
            (valid_df['temp'] > -5) & (valid_df['temp'] < 50) &
            (valid_df['psal'] > 0) & (valid_df['psal'] < 50) &
            (valid_df['pressure'] > 0)
        ]

        return valid_df

    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database contents."""
        try:
            stats = {}

            # Count floats
            engine = self._get_engine()
            float_count = pd.read_sql(text("SELECT COUNT(*) as count FROM floats"), engine)
            stats['total_floats'] = int(float_count.iloc[0]['count'])

            # Count profiles
            profile_count = pd.read_sql(text("SELECT COUNT(*) as count FROM profiles"), engine)
            stats['total_profiles'] = int(profile_count.iloc[0]['count'])

            # Count measurements
            measurement_count = pd.read_sql(text("SELECT COUNT(*) as count FROM measurements"), engine)
            stats['total_measurements'] = int(measurement_count.iloc[0]['count'])

            # Date range
            date_range = pd.read_sql(text("""
                SELECT
                    MIN(profile_date) as min_date,
                    MAX(profile_date) as max_date
                FROM profiles
            """), engine)

            stats['date_range'] = {
                'min': date_range.iloc[0]['min_date'],
                'max': date_range.iloc[0]['max_date']
            }

            # Geographic bounds
            geo_bounds = pd.read_sql(text("""
                SELECT
                    MIN(ST_Y(location::geometry)) as min_lat,
                    MAX(ST_Y(location::geometry)) as max_lat,
                    MIN(ST_X(location::geometry)) as min_lon,
                    MAX(ST_X(location::geometry)) as max_lon
                FROM profiles
            """), engine)

            stats['geographic_bounds'] = {
                'lat_min': float(geo_bounds.iloc[0]['min_lat']),
                'lat_max': float(geo_bounds.iloc[0]['max_lat']),
                'lon_min': float(geo_bounds.iloc[0]['min_lon']),
                'lon_max': float(geo_bounds.iloc[0]['max_lon'])
            }

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}
